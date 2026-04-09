import { useEffect, useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import type { Card } from "@/lib/kanban";

type KanbanCardProps = {
  card: Card;
  onDelete: (cardId: string) => Promise<boolean> | boolean;
  onUpdate: (
    cardId: string,
    title: string,
    details: string
  ) => Promise<boolean> | boolean;
};

const EditIcon = () => (
  <svg
    aria-hidden="true"
    viewBox="0 0 20 20"
    className="h-4 w-4"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M3.75 14.75 3 17l2.25-.75L15.5 6 14 4.5 3.75 14.75Z" />
    <path d="m13.5 5 1.5-1.5a1.06 1.06 0 0 1 1.5 0l.5.5a1.06 1.06 0 0 1 0 1.5L15.5 7" />
  </svg>
);

const DeleteIcon = () => (
  <svg
    aria-hidden="true"
    viewBox="0 0 20 20"
    className="h-4 w-4"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M4.5 6h11" />
    <path d="M7.25 6V4.75c0-.41.34-.75.75-.75h4c.41 0 .75.34.75.75V6" />
    <path d="M6.25 6 7 15.5c.04.86.74 1.5 1.6 1.5h2.8c.86 0 1.56-.64 1.6-1.5l.75-9.5" />
    <path d="M8.5 9v5" />
    <path d="M11.5 9v5" />
  </svg>
);

export const KanbanCard = ({ card, onDelete, onUpdate }: KanbanCardProps) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({
      id: card.id,
      transition: {
        duration: 220,
        easing: "cubic-bezier(0.22, 1, 0.36, 1)",
      },
    });
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(card.title);
  const [details, setDetails] = useState(card.details);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  useEffect(() => {
    setTitle(card.title);
    setDetails(card.details);
  }, [card.details, card.title]);

  const handleSave = async () => {
    const nextTitle = title.trim();
    if (!nextTitle) {
      return;
    }

    setIsSaving(true);
    const didSave = await onUpdate(card.id, nextTitle, details.trim());
    setIsSaving(false);

    if (didSave) {
      setIsEditing(false);
    }
  };

  return (
    <article
      ref={setNodeRef}
      style={style}
      className={clsx(
        "rounded-2xl border border-transparent bg-white px-4 py-4 shadow-[0_12px_24px_rgba(3,33,71,0.08)]",
        "transition-[box-shadow,opacity] duration-200 ease-out",
        isDragging && "opacity-60 shadow-[0_18px_32px_rgba(3,33,71,0.16)]"
      )}
      data-testid={`card-${card.id}`}
    >
      <div
        className="w-full"
        {...(isEditing ? {} : attributes)}
        {...(isEditing ? {} : listeners)}
      >
        {isEditing ? (
          <div>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              className="w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm font-semibold text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
              aria-label={`Edit ${card.title} title`}
            />
            <textarea
              value={details}
              onChange={(event) => setDetails(event.target.value)}
              rows={3}
              className="mt-3 w-full resize-none rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--gray-text)] outline-none transition focus:border-[var(--primary-blue)]"
              aria-label={`Edit ${card.title} details`}
            />
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => {
                  void handleSave();
                }}
                disabled={isSaving}
                className="rounded-full bg-[var(--secondary-purple)] px-3 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110"
              >
                {isSaving ? "Saving..." : "Save"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setTitle(card.title);
                  setDetails(card.details);
                  setIsEditing(false);
                }}
                disabled={isSaving}
                className="rounded-full border border-[var(--stroke)] px-3 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div className="flex items-start gap-3">
              <h4 className="min-w-0 flex-1 pr-1 font-display text-base font-semibold text-[var(--navy-dark)]">
                {card.title}
              </h4>
              <div className="flex shrink-0 items-center gap-1">
                <button
                  type="button"
                  onPointerDown={(event) => event.stopPropagation()}
                  onClick={() => setIsEditing(true)}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-full text-[var(--gray-text)] transition hover:bg-[var(--surface)] hover:text-[var(--navy-dark)]"
                  aria-label={`Edit ${card.title}`}
                >
                  <EditIcon />
                </button>
                <button
                  type="button"
                  onPointerDown={(event) => event.stopPropagation()}
                  onClick={() => {
                    if (isDeleting) return;
                    setIsDeleting(true);
                    void Promise.resolve(onDelete(card.id)).finally(() =>
                      setIsDeleting(false)
                    );
                  }}
                  disabled={isDeleting}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-full text-[var(--gray-text)] transition hover:bg-[var(--surface)] hover:text-[var(--navy-dark)] disabled:opacity-40"
                  aria-label={`Delete ${card.title}`}
                >
                  <DeleteIcon />
                </button>
              </div>
            </div>
            <p className="mt-2 w-full text-sm leading-6 text-[var(--gray-text)]">
              {card.details}
            </p>
          </div>
        )}
      </div>
    </article>
  );
};
