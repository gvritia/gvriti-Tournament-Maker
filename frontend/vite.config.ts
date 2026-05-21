import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// Tournament Maker — Vite config.
//
// `base` is configurable so the same build can be served from:
//   * a custom domain root (`/`),
//   * a Docker container behind a reverse proxy,
//   * GitHub Pages under a repo path (`/<repo-name>/`).
//
// When running `npm run build:pages` (or via the GitHub Actions workflow)
// Vite reads the `pages` mode env file and sets `base` to that value.
// The default dev server still serves from `/`.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const explicitBase = env.VITE_BASE_PATH ?? "";
  const isPagesBuild = mode === "pages";
  const repoFromCi = env.GITHUB_REPOSITORY
    ? `/${env.GITHUB_REPOSITORY.split("/").pop()}/`
    : "";

  const base =
    explicitBase ||
    (isPagesBuild ? repoFromCi || "/gvriti-Tournament-Maker/" : "/");

  return {
    plugins: [react()],
    base,
    server: {
      port: 5173,
      strictPort: false,
    },
  };
});
