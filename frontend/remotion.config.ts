// See all configuration options: https://remotion.dev/docs/config
// Each option also is available as a CLI flag: https://remotion.dev/docs/cli

// Note: When using the Node.JS APIs, the config file doesn't apply. Instead, pass options directly to the APIs

import { Config } from "@remotion/cli/config";
import { webpackOverride } from "./src/remotion/webpack-override.mjs";
Config.overrideWebpackConfig(webpackOverride);
Config.setPublicDir("./public");
Config.setEntryPoint("./src/remotion/index.ts");

