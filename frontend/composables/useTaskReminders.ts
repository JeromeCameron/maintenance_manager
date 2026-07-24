import type { Task } from "~/types"

const DUE_SOON_DAYS = 3
const DONE_STATUSES = ["completed", "archived"]

export function useTaskReminders() {
  const { getAll } = useTasks()
  const { user } = useAuth()

  const { data: tasks, refresh } = useAsyncData("task-reminders", () => getAll())

  const dueSoon = computed<Task[]>(() => {
    if (!user.value) return []
    const threshold = new Date()
    threshold.setDate(threshold.getDate() + DUE_SOON_DAYS)
    const thresholdStr = threshold.toISOString().slice(0, 10)

    return (tasks.value ?? [])
      .filter((t) =>
        (t.assigned_to === user.value!.user_id || t.user_id === user.value!.user_id) &&
        !DONE_STATUSES.includes(t.status) &&
        !!t.due_date &&
        t.due_date <= thresholdStr
      )
      .sort((a, b) => (a.due_date ?? "").localeCompare(b.due_date ?? ""))
  })

  function isOverdue(task: Task): boolean {
    if (!task.due_date) return false
    return task.due_date < new Date().toISOString().slice(0, 10)
  }

  return { dueSoon, refresh, isOverdue }
}
