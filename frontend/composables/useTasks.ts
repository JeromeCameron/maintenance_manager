import type { Task } from "~/types"

export function useTasks() {
  const { get, post, put, del } = useApi()

  const getAll = () => get<Task[]>("/tasks")
  const getOne = (id: number) => get<Task>(`/tasks/${id}`)
  const create = (data: Task) => post<Task>("/tasks", data)
  const update = (id: number, data: Task) => put<Task>(`/tasks/${id}`, data)
  const remove = (id: number) => del(`/tasks/${id}`)

  return { getAll, getOne, create, update, remove }
}
