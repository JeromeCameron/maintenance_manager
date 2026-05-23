export default defineNuxtConfig({
  modules: ["@nuxt/ui"],

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE ?? "http://localhost:8000/api",
    },
  },

  compatibilityDate: "2025-05-23",
})
