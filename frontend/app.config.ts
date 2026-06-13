export default defineAppConfig({
  ui: {
    colors: {
      primary: "blue",
      neutral: "slate",
    },
    table: {
      slots: {
        root: "relative overflow-auto max-h-[calc(100vh-15rem)]",
        thead: "sticky top-0 z-10 bg-white",
      },
    },
  },
})
