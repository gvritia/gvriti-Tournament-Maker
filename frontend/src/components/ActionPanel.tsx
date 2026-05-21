import { Lock } from "lucide-react";
import type { ReactNode } from "react";

export type PreviewAction = {
  label: string;
  icon?: ReactNode;
  tone?: "primary" | "danger" | "neutral";
};

type ActionPanelProps = {
  title: string;
  description: string;
  actions: PreviewAction[];
};

export function ActionPanel({ title, description, actions }: ActionPanelProps) {
  return (
    <section className="panel action-panel">
      <div>
        <p className="eyebrow">Action panel</p>
        <h2>{title}</h2>
        <p className="muted">{description}</p>
      </div>
      <div className="action-list">
        {actions.map((action) => (
          <button
            key={action.label}
            className={`button button-${action.tone ?? "neutral"}`}
            type="button"
            disabled
            title="Действие доступно только после входа"
          >
            {action.icon ?? <Lock size={16} />}
            {action.label}
          </button>
        ))}
      </div>
    </section>
  );
}
