// See all configuration options: https://remotion.dev/docs/config
// Each option also is available as a CLI flag: https://remotion.dev/docs/cli

// Note: When using the Node.JS APIs, the config file doesn't apply. Instead, pass options directly to the APIs

import { Config } from "@remotion/cli/config";
import { webpackOverride } from "./remotion/webpack-override.mjs";
Config.setConcurrency(8);
Config.setCodec("h264");
Config.setVideoImageFormat("jpeg");
Config.overrideWebpackConfig(webpackOverride);
Config.setPublicDir("./public");
Config.setEntryPoint("./remotion/index.ts");

