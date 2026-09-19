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
        <Dialog.Overlay className="fixed inset-0 z-40 bg-slate-900/40" />
        <Dialog.Content className="fixed start-1/2 top-1/2 z-50 w-[min(90vw,28rem)] -translate-x-1/2 rtl:translate-x-1/2 -translate-y-1/2 rounded-2xl bg-white p-6 shadow-xl">
          <Dialog.Title className="text-xl font-bold">{title}</Dialog.Title>
          <Dialog.Description className="my-4 text-slate-600">
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
