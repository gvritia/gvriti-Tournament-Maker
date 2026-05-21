import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

type ConfirmationTone = "primary" | "danger";

type ConfirmationOptions = {
  title?: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: ConfirmationTone;
};

type ConfirmationRequest = Required<ConfirmationOptions> & {
  resolve: (confirmed: boolean) => void;
};

const DEFAULT_TITLE = "Подтвердите действие";
const DEFAULT_CONFIRM_LABEL = "OK";
const DEFAULT_CANCEL_LABEL = "Отмена";

export function useConfirmationDialog() {
  const [request, setRequest] = useState<ConfirmationRequest | null>(null);

  function confirm(options: ConfirmationOptions) {
    return new Promise<boolean>((resolve) => {
      setRequest({
        title: options.title ?? DEFAULT_TITLE,
        message: options.message,
        confirmLabel: options.confirmLabel ?? DEFAULT_CONFIRM_LABEL,
        cancelLabel: options.cancelLabel ?? DEFAULT_CANCEL_LABEL,
        tone: options.tone ?? "primary",
        resolve,
      });
    });
  }

  function close(confirmed: boolean) {
    request?.resolve(confirmed);
    setRequest(null);
  }

  const dialog = request ? (
    <ConfirmationDialog
      title={request.title}
      message={request.message}
      confirmLabel={request.confirmLabel}
      cancelLabel={request.cancelLabel}
      tone={request.tone}
      onCancel={() => close(false)}
      onConfirm={() => close(true)}
    />
  ) : null;

  return { confirm, dialog };
}

function ConfirmationDialog({
  title,
  message,
  confirmLabel,
  cancelLabel,
  tone,
  onCancel,
  onConfirm,
}: {
  title: string;
  message: string;
  confirmLabel: string;
  cancelLabel: string;
  tone: ConfirmationTone;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onCancel();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onCancel]);

  const confirmClassName =
    tone === "danger" ? "button button-danger" : "button button-primary";

  return createPortal(
    <div className="confirmation-overlay" role="presentation" onMouseDown={onCancel}>
      <section
        aria-labelledby="confirmation-dialog-title"
        aria-modal="true"
        className="confirmation-dialog"
        role="dialog"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div>
          <p className="eyebrow">{title}</p>
          <h2 id="confirmation-dialog-title">{message}</h2>
        </div>
        <div className="confirmation-actions">
          <button className={confirmClassName} type="button" onClick={onConfirm}>
            {confirmLabel}
          </button>
          <button className="button button-ghost" type="button" onClick={onCancel}>
            {cancelLabel}
          </button>
        </div>
      </section>
    </div>,
    document.body,
  );
}
