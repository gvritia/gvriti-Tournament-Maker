const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export type ApiError = Error & {
  status?: number;
  fieldErrors?: Record<string, string>;
};

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  token?: string | null;
  timeoutMs?: number;
};

export async function apiRequest<T>(
  path: string,
  { method = "GET", body, token, timeoutMs = 8000 }: RequestOptions = {},
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });

    if (response.status === 204) {
      return undefined as T;
    }

    const payload = await parseJson(response);

    if (!response.ok) {
      throw normalizeApiError(response.status, payload);
    }

    return payload as T;
  } catch (error) {
    if (isApiError(error)) {
      throw error;
    }

    if (isAbortError(error)) {
      const timeoutError = new Error(
        "Сервер долго отвечает. Дождитесь завершения операции или обновите страницу через несколько секунд.",
      ) as ApiError;
      timeoutError.status = 0;
      throw timeoutError;
    }

    const networkError = new Error(
      "Сервер недоступен. Проверьте соединение и попробуйте снова.",
    ) as ApiError;
    networkError.status = 0;
    throw networkError;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

export async function getAllPages<T>(
  path: string,
  token: string,
  limit = 100,
): Promise<T[]> {
  const rows: T[] = [];
  let offset = 0;

  while (true) {
    const separator = path.includes("?") ? "&" : "?";
    const page = await apiRequest<T[]>(
      `${path}${separator}offset=${offset}&limit=${limit}`,
      { token },
    );
    rows.push(...page);

    if (page.length < limit) {
      return rows;
    }

    offset += limit;
  }
}

async function parseJson(response: Response) {
  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

function normalizeApiError(status: number, payload: unknown): ApiError {
  const message = humanizeError(status, payload);
  const error = new Error(message) as ApiError;
  error.status = status;

  if (status === 422 && typeof payload === "object" && payload !== null) {
    error.fieldErrors = extractFieldErrors(payload);
  }

  return error;
}

function humanizeError(status: number, payload: unknown): string {
  const detail = extractDetail(payload);

  if (detail) {
    return translateBackendDetail(detail, status);
  }

  switch (status) {
    case 400:
      return "Запрос нарушает бизнес-правила.";
    case 401:
      return "Нужно войти в аккаунт.";
    case 403:
      return "У вас нет доступа к этому действию.";
    case 404:
      return "Запись не найдена.";
    case 409:
      return "Конфликт данных. Проверьте расписание или уникальность полей.";
    case 422:
      return "Проверьте поля формы.";
    default:
      return "Не удалось выполнить запрос.";
  }
}

function extractDetail(payload: unknown): string | null {
  if (typeof payload === "string") {
    return payload;
  }

  if (typeof payload !== "object" || payload === null || !("detail" in payload)) {
    return null;
  }

  const detail = (payload as { detail: unknown }).detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return "Проверьте поля формы.";
  }

  return null;
}

function extractFieldErrors(payload: object): Record<string, string> {
  if (!("detail" in payload)) {
    return {};
  }

  const detail = (payload as { detail: unknown }).detail;
  if (!Array.isArray(detail)) {
    return {};
  }

  return detail.reduce<Record<string, string>>((errors, item) => {
    if (typeof item !== "object" || item === null) {
      return errors;
    }

    const location = "loc" in item ? item.loc : undefined;
    const message = "msg" in item ? item.msg : undefined;

    if (Array.isArray(location) && typeof message === "string") {
      const field = String(location[location.length - 1]);
      errors[field] = translateFieldError(field, message);
    }

    return errors;
  }, {});
}

function translateBackendDetail(detail: string, status: number): string {
  const normalized = detail.trim().toLowerCase();
  const knownMessages: Record<string, string> = {
    "a team with this name already exists.":
      "Команда с таким названием уже существует.",
    "a season with this name already exists.":
      "Сезон с таким названием уже существует.",
    "a stadium with this name already exists.":
      "Стадион с таким названием уже существует.",
    "a referee with this name already exists.":
      "Судья с таким именем уже существует.",
    "a referee with this full name already exists.":
      "Судья с таким именем уже существует.",
    "a tournament with this name already exists in the season.":
      "В этом сезоне уже есть турнир с таким названием.",
    "a tournament with this name already exists in this season.":
      "В этом сезоне уже есть турнир с таким названием.",
    "this team already has a player with this number.":
      "В этой команде уже есть игрок с таким номером.",
    "player is already in this match lineup.":
      "Этот игрок уже добавлен в состав на этот матч.",
    "this team already has this number in the lineup.":
      "В составе этой команды уже есть игрок с таким номером.",
    "player is suspended for this match.":
      "Этот игрок дисквалифицирован на ближайший матч.",
    "this team already has a lineup for this match.":
      "Для этой команды уже есть состав на этот матч. Включите замену состава, если хотите сгенерировать его заново.",
    "team has no players for lineup generation.":
      "В команде нет игроков для генерации состава.",
    "not enough eligible players for lineup generation.":
      "Недостаточно доступных игроков для генерации состава.",
    "could not generate a valid starting lineup with exactly one goalkeeper.":
      "Не удалось собрать стартовый состав ровно с одним вратарём.",
    "preferred player ids must be unique.":
      "В списке предпочтительных игроков не должно быть повторов.",
    "team is not a participant of this match.":
      "Выбранная команда не участвует в этом матче.",
    "player does not belong to this team.":
      "Выбранный игрок не относится к этой команде.",
    "final score must match recorded goal events.":
      "Итоговый счёт должен совпадать с голами, внесёнными в протокол.",
    "match protocol cannot be changed after match is finished or cancelled.":
      "Протокол завершённого или отменённого матча нельзя менять.",
    "cancelled match cannot be finished.":
      "Отменённый матч нельзя завершить.",
    "match is already finished.": "Матч уже завершён.",
    "random result cannot be generated for finished or cancelled matches.":
      "Для завершённого или отменённого матча нельзя сгенерировать результат.",
    "random result cannot be generated for a match with protocol events.":
      "Нельзя сгенерировать протокол, если в матче уже есть события.",
    "random result generation requires players for both teams.":
      "Для генерации протокола нужны игроки в обеих командах.",
    "protocol generation requires a referee or at least one referee available for automatic assignment.":
      "Для генерации протокола назначьте судью или добавьте хотя бы одного доступного судью.",
    "no referee is available for protocol generation.":
      "Нет доступного судьи для генерации протокола.",
    "protocol generation requires each existing team lineup to have at least 11 starters.":
      "Для генерации протокола в каждом существующем составе должно быть минимум 11 игроков основы.",
    "protocol generation requires each starting lineup to have exactly one goalkeeper.":
      "Для генерации протокола в каждом стартовом составе должен быть ровно один вратарь.",
    "protocol generation requires an eligible goalkeeper for each team.":
      "Для генерации протокола каждой команде нужен доступный вратарь.",
    "protocol generation requires at least ten eligible field players for each team.":
      "Для генерации протокола каждой команде нужны минимум десять доступных полевых игроков.",
    "protocol generation requires match lineups.":
      "Для генерации протокола нужны составы обеих команд.",
    "season has no matches to generate.":
      "В сезоне нет матчей для генерации протоколов.",
    "home and away teams must be different.":
      "Домашняя и гостевая команды должны отличаться.",
    "home team and away team must be different.":
      "Домашняя и гостевая команды должны отличаться.",
    "match cannot be created with finished status.":
      "Новый матч нельзя сразу создать завершённым.",
    "match season must match tournament season.":
      "Сезон матча должен совпадать с сезоном турнира.",
    "finished match cannot be edited or deleted.":
      "Завершённый матч нельзя редактировать или удалять.",
    "a team cannot play more than one match per day.":
      "Команда не может играть больше одного матча в день.",
    "a team cannot play more than two matches per week.":
      "Команда не может играть больше двух матчей в неделю.",
    "referee is already assigned to a parallel match.":
      "Судья уже назначен на другой матч в это время.",
    "referee is already assigned to a parallel generated match.":
      "Судья уже назначен на другой матч в создаваемом расписании.",
    "referee is already assigned to another match at this time.":
      "Судья уже назначен на другой матч в это время.",
    "championship schedule can be generated only for championship tournaments.":
      "Расписание чемпионата можно создать только для турнира типа championship.",
    "team ids must be unique.": "Выберите разные команды.",
    "team ids must be positive.": "Выберите команды из списка.",
    "each team needs a home stadium, team stadium mapping, or fallback stadium.":
      "Для каждой команды нужен домашний стадион, ручная привязка или резервный стадион.",
    "stadium mapping can contain only teams from the generated schedule.":
      "В привязке стадионов могут быть только команды из выбранного расписания.",
    "could not generate schedule because of a conflict.":
      "Не удалось создать расписание из-за конфликта данных.",
    "cup semifinals already exist.": "Полуфиналы кубка уже созданы.",
    "cup final already exists.": "Финал кубка уже создан.",
    "cup final requires exactly two semifinals.":
      "Для финала кубка нужны ровно два полуфинала.",
    "cup bracket can be managed only for cup tournaments.":
      "Кубковая сетка доступна только для турниров типа cup.",
    "cup semifinals require four unique teams.":
      "Для полуфиналов кубка нужны четыре разные команды.",
    "provide either manual team_ids or use previous season places.":
      "Выберите команды вручную или используйте места прошлого сезона, но не оба варианта сразу.",
    "automatic cup semifinal selection requires at least four teams with previous season places.":
      "Для автоподбора полуфиналов нужны минимум четыре команды с местами прошлого сезона.",
    "cup semifinal generation requires four selected team ids.":
      "Для полуфиналов кубка выберите четыре команды.",
    "stadium mapping can contain only teams from the cup semifinals.":
      "В привязке стадионов могут быть только команды полуфиналов.",
    "each cup semifinal home team needs a home stadium, team stadium mapping, or fallback stadium.":
      "Для домашних команд полуфиналов нужен домашний стадион, ручная привязка или резервный стадион.",
    "cup match winner cannot be determined from an unfinished or drawn match.":
      "Нельзя определить победителя кубкового матча: он не завершён или закончился вничью.",
    "could not generate cup semifinals because of a conflict.":
      "Не удалось создать полуфиналы кубка из-за конфликта данных.",
    "could not find an available cup match date for the selected teams.":
      "Не удалось найти свободную дату для кубкового матча выбранных команд.",
    "could not generate cup final because of a conflict.":
      "Не удалось создать финал кубка из-за конфликта данных.",
  };

  if (knownMessages[normalized]) {
    return knownMessages[normalized];
  }

  if (
    normalized.includes("emblem_url") &&
    normalized.includes("http") &&
    normalized.includes("https")
  ) {
    return "Введите HTTP/HTTPS ссылку на логотип команды.";
  }

  if (
    normalized.includes("traceback") ||
    normalized.includes("stack") ||
    normalized.includes("http://") ||
    normalized.includes("https://")
  ) {
    return fallbackErrorMessage(status);
  }

  return detail;
}

function translateFieldError(field: string, message: string): string {
  const normalized = message.trim().toLowerCase();

  if (
    field === "emblem_url" &&
    normalized.includes("http") &&
    normalized.includes("https")
  ) {
    return "Введите HTTP/HTTPS ссылку на логотип команды.";
  }

  if (normalized.includes("field required")) {
    return "Заполните это поле.";
  }

  if (normalized.includes("input should be a valid integer")) {
    return "Введите целое число.";
  }

  if (normalized.includes("input should be greater than")) {
    return "Введите значение больше минимального.";
  }

  if (normalized.includes("input should be a valid decimal")) {
    return "Введите корректное число.";
  }

  return message;
}

function fallbackErrorMessage(status: number): string {
  switch (status) {
    case 400:
      return "Запрос нарушает бизнес-правила.";
    case 401:
      return "Нужно войти в аккаунт.";
    case 403:
      return "У вас нет доступа к этому действию.";
    case 404:
      return "Запись не найдена.";
    case 409:
      return "Конфликт данных. Проверьте расписание или уникальность полей.";
    case 422:
      return "Проверьте поля формы.";
    default:
      return "Не удалось выполнить запрос.";
  }
}

function isApiError(error: unknown): error is ApiError {
  return error instanceof Error && "status" in error;
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}
