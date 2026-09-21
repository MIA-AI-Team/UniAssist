"use client";
import * as Dialog from "@radix-ui/react-alert-dialog";
import { useTranslations } from "next-intl";
import { Button } from "./button";
export function Confirm({
  title,
  description,
  onConfirm,
  disabled = false,
  destructive = false,
}: {
  title: string;
  description: string;
  onConfirm: () => void;
  disabled?: boolean;
  destructive?: boolean;
}) {
  const t = useTranslations();
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <Button
          disabled={disabled}
          variant={destructive ? "destructive" : "default"}
        >
          {title}
        </Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog-content">
          <Dialog.Title className="text-xl font-bold">{title}</Dialog.Title>
          <Dialog.Description className="my-4 text-muted">
            {description}
          </Dialog.Description>
          <div className="flex justify-end gap-3">
            <Dialog.Cancel asChild>
              <Button variant="outline">{t("cancel")}</Button>
            </Dialog.Cancel>
            <Dialog.Action asChild>
              <Button
                variant={destructive ? "destructive" : "default"}
                onClick={onConfirm}
              >
                {t("confirm")}
              </Button>
            </Dialog.Action>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
