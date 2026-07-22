export default defineAppConfig({
  ui: {
    colors: {
      primary: "blue",
      neutral: "slate",
    },
    table: {
      slots: {
        root: "relative overflow-auto max-h-[calc(100vh-15rem)]",
        thead: "sticky top-0 z-10 bg-white dark:bg-slate-900",
        th: "px-4 py-3.5 text-xs text-highlighted text-left rtl:text-right font-semibold [&:has([role=checkbox])]:pe-0",
        td: "p-4 text-xs text-muted whitespace-nowrap [&:has([role=checkbox])]:pe-0",
      },
    },
  },
})
