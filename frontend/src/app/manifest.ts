import type { MetadataRoute } from "next";

// Lets a farmer "Add to Home screen" from the browser: opens like an app,
// with no app-store download.
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "किसान साथी",
    short_name: "किसान साथी",
    description: "Daily crop advice for your farm in Marathi, Hindi and English",
    start_url: "/kisan",
    display: "standalone",
    background_color: "#f3f8f4",
    theme_color: "#0b3d2a",
    icons: [{ src: "/kisan-icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" }],
  };
}
