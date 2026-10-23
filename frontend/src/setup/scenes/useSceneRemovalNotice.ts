import { h, onScopeDispose } from "vue"
import { toast } from "vue-sonner"

import SceneRemovalNotice from "./SceneRemovalNotice.vue"
import type { ProfileEditor } from "@/setup/profile/useProfileDraft"

/** 每次移除保留独立撤销能力，保存期间禁用，离开会话时一并释放提示。 */
export function useSceneRemovalNotice(editor: ProfileEditor, onEdit: () => void) {
  const notifications = new Set<string | number>()
  onScopeDispose(() => notifications.forEach((id) => toast.dismiss(id)))

  return function removeScene(id: string): void {
    const removed = editor.removeScene(id)
    onEdit()
    function dismiss(): void {
      toast.dismiss(notification)
      notifications.delete(notification)
    }
    const notification = toast.custom(
      () =>
        h(SceneRemovalNotice, {
          locale: editor.locale.value,
          name: removed.name,
          submitting: editor.submitting.value,
          onDismiss: dismiss,
          onRestore: () => {
            if (editor.submitting.value) return
            removed.restore()
            onEdit()
            dismiss()
          },
        }),
      { duration: Infinity, onDismiss: () => notifications.delete(notification) },
    )
    notifications.add(notification)
  }
}
