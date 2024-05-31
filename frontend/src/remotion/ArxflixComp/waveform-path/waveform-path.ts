/* eslint-disable */
import type { LinearPathOptions, PolarPathOptions } from "./types";

export function linearPath(frequenciesToDisplay: number[], options: LinearPathOptions) {
  const {
    samples = frequenciesToDisplay.length,
    normalizeFactor = 1,
    height = 100,
    width = 800,
    top = 0,
    left = 0,
    type = "steps",
    paths = [
      { d: "Q", sx: 0, sy: 0, x: 50, y: 100, ex: 100, ey: 0 },
    ] as LinearPathOptions["paths"],
  } = options;

  const normalizeData = frequenciesToDisplay.map((n) => n * normalizeFactor);
  let path = ``;

  const fixHeight = type != "bars" ? (height + top * 2) / 2 : height + top;
  const fixWidth = width / samples;
  const pathslength = paths.length;
  const fixpathslength = type == "mirror" ? pathslength * 2 : pathslength;

  let last_pos_x = -9999;
  let last_pos_y = -9999;

  for (let i = 0; i < samples; i++) {
    const positive = type != "bars" ? (i % 2 ? 1 : -1) : 1;
    let mirror = 1;
    for (let j = 0; j < fixpathslength; j++) {
      let k = j;
      if (j >= pathslength) {
        k = j - pathslength;
        mirror = -1;
      }
      const currentPath = paths[k];
      currentPath.minshow = currentPath.minshow ?? 0;
      currentPath.maxshow = currentPath.maxshow ?? 1;
      currentPath.normalize = currentPath.normalize ?? false;
      const normalizeDataValue = currentPath.normalize
        ? 1
        : normalizeData[i];
      if (
        currentPath.minshow <= normalizeData[i] &&
        currentPath.maxshow >= normalizeData[i]
      ) {
        switch (currentPath.d) {
          // LineTo Commands
          case "L": {
            const pos_x =
              i * fixWidth + (fixWidth * currentPath.sx) / 100 + left;
            const pos_y =
              fixHeight +
              ((normalizeDataValue * currentPath.sy) / 100) *
              (type != "bars" ? height / 2 : height) *
              -positive *
              mirror;

            const end_pos_x =
              i * fixWidth + (fixWidth * currentPath.ex) / 100 + left;
            const end_pos_y =
              fixHeight +
              ((normalizeDataValue * currentPath.ey) / 100) *
              (type != "bars" ? height / 2 : height) *
              -positive *
              mirror;

            if (pos_x !== last_pos_x || pos_y !== last_pos_y) {
              path += `M ${pos_x} ${pos_y} `;
            }

            path += `L ${end_pos_x} ${end_pos_y} `;

            last_pos_x = end_pos_x;
            last_pos_y = end_pos_y;
            break;
          }

          case "H": {
            const pos_x =
              i * fixWidth + (fixWidth * currentPath.sx) / 100 + left;
            const pos_y =
              fixHeight +
              ((normalizeDataValue * currentPath.y) / 100) *
              (type != "bars" ? height / 2 : height) *
              -positive *
              mirror;

            const end_pos_x =
              i * fixWidth + (fixWidth * currentPath.ex) / 100 + left;
            const end_pos_y = pos_y;

            if (pos_x !== last_pos_x || pos_y !== last_pos_y) {
              path += `M ${pos_x} ${pos_y} `;
            }

            path += `H ${end_pos_x} `;

            last_pos_x = end_pos_x;
            last_pos_y = end_pos_y;
            break;
          }

          case "V": {
            const pos_x =
              i * fixWidth + (fixWidth * currentPath.x) / 100 + left;
            const pos_y =
              fixHeight +
              ((normalizeDataValue * currentPath.sy) / 100) *
              (type != "bars" ? height / 2 : height) *
              -positive *
              mirror;

            const end_pos_x = pos_x;
            const end_pos_y =
              fixHeight +
              ((normalizeDataValue * currentPath.ey) / 100) *
              (type != "bars" ? height / 2 : height) *
              -positive *
              mirror;

            if (pos_x !== last_pos_x || pos_y !== last_pos_y) {
              path += `M ${pos_x} ${pos_y} `;
            }

            path += `V ${end_pos_y} `;

            last_pos_x = end_pos_x;
            last_pos_y = end_pos_y;
            break;
          }

          // Cubic Bézier Curve Commands
          case "C": {
            const pos_x =
              i * fixWidth + (fixWidth * currentPath.sx) / 100 + left;
            const pos_y =
              fixHeight - ((fixHeight * currentPath.sy) / 100) * positive;

            const center_pos_x =
              i * fixWidth + (fixWidth * currentPath.x) / 100 + left;
            const center_pos_y =
              fixHeight +
              ((normalizeDataValue * currentPath.y) / 100) *
              (type != "bars" ? height : height * 2) *
              -positive *
              mirror;

            const end_pos_x =
              i * fixWidth + (fixWidth * currentPath.ex) / 100 + left;
            const end_pos_y =
              fixHeight - ((fixHeight * currentPath.ey) / 100) * positive;

            if (pos_x !== last_pos_x || pos_y !== last_pos_y) {
              path += `M ${pos_x} ${pos_y} `;
            }

            path += `C ${pos_x} ${pos_y} ${center_pos_x} ${center_pos_y} ${end_pos_x} ${end_pos_y} `;

            last_pos_x = end_pos_x;
            last_pos_y = end_pos_y;
            break;
          }

          // Quadratic Bézier Curve Commands
          case "Q": {
            const pos_x =
              i * fixWidth + (fixWidth * currentPath.sx) / 100 + left;
            const pos_y =
              fixHeight +
              ((normalizeDataValue * currentPath.sy) / 100) *
              (type != "bars" ? height / 2 : height) *
              -positive *
              mirror;

            const center_pos_x =
              i * fixWidth + (fixWidth * currentPath.x) / 100 + left;
            const center_pos_y =
              fixHeight +
              ((normalizeDataValue * currentPath.y) / 100) *
              (type != "bars" ? height : height * 2) *
              -positive *
              mirror;

            const end_pos_x =
              i * fixWidth + (fixWidth * currentPath.ex) / 100 + left;
            const end_pos_y =
              fixHeight +
              ((normalizeDataValue * currentPath.ey) / 100) *
              (type != "bars" ? height / 2 : height) *
              -positive *
              mirror;

            if (pos_x !== last_pos_x || pos_y !== last_pos_y) {
              path += `M ${pos_x} ${pos_y} `;
            }

            path += `Q ${center_pos_x} ${center_pos_y} ${end_pos_x} ${end_pos_y} `;

            last_pos_x = end_pos_x;
            last_pos_y = end_pos_y;
            break;
          }

          // Elliptical Arc Curve Commands
          case "A": {
            const pos_x =
              i * fixWidth + (fixWidth * currentPath.sx) / 100 + left;
            const pos_y =
              fixHeight +
              ((normalizeDataValue * currentPath.sy) / 100) *
              (type != "bars" ? height / 2 : height) *
              -positive *
              mirror;

            const end_pos_x =
              i * fixWidth + (fixWidth * currentPath.ex) / 100 + left;
            const end_pos_y =
              fixHeight +
              ((normalizeDataValue * currentPath.ey) / 100) *
              (type != "bars" ? height / 2 : height) *
              -positive *
              mirror;

            if (pos_x !== last_pos_x || pos_y !== last_pos_y) {
              path += `M ${pos_x} ${pos_y} `;
            }
            const rx = (currentPath.rx * fixWidth) / 100;
            const ry = (currentPath.ry * fixWidth) / 100;
            let { sweep } = currentPath;
            if (positive == -1) {
              if (sweep == 1) {
                sweep = 0;
              } else {
                sweep = 1;
              }
            }
            if (mirror == -1) {
              if (sweep == 1) {
                sweep = 0;
              } else {
                sweep = 1;
              }
            }
            path += `A ${rx} ${ry} ${currentPath.angle} ${currentPath.arc} ${sweep} ${end_pos_x} ${end_pos_y} `;

            last_pos_x = end_pos_x;
            last_pos_y = end_pos_y;
            break;
          }

          // ClosePath Commands
          case "Z":
            path += "Z ";
            break;

          default:
            break;
        }
      }
    }
  }
  return path;
}

export function polarPath(frequenciesToDisplay: number[], options: PolarPathOptions) {
  const {
    samples = frequenciesToDisplay.length,
    distance = 50,
    length = 100,
    top = 0,
    left = 0,
    type = "steps",
    startdeg = 0,
    enddeg = 360,
    invertdeg = false,
    invertpath = false,
    paths = [
      { d: "Q", sdeg: 0, sr: 0, deg: 50, r: 100, edeg: 100, er: 0 },
    ] as PolarPathOptions["paths"],
    normalizeFactor = 1
  } = options;

  const normalizeData = frequenciesToDisplay.map((n) => n * normalizeFactor);
  let path = ``;
  const fixenddeg = enddeg < startdeg ? enddeg + 360 : enddeg;
  const deg = !invertdeg
    ? (fixenddeg - startdeg) / samples
    : (startdeg - fixenddeg) / samples;
  const fixOrientation = !invertdeg ? 90 + startdeg : 90 + startdeg + 180;
  const invert = !invertpath ? 1 : -1;
  const pathslength = paths.length;
  const fixpathslength = type == "mirror" ? pathslength * 2 : pathslength;
  const pi180 = Math.PI / 180;

  let last_pos_x = -9999;
  let last_pos_y = -9999;

  for (let i = 0; i < samples; i++) {
    const positive = type != "bars" ? (i % 2 ? 1 : -1) : 1;
    let mirror = 1;
    for (let j = 0; j < fixpathslength; j++) {
      let k = j;
      if (j >= pathslength) {
        k = j - pathslength;
        mirror = -1;
      }
      const currentPath = paths[k];
      currentPath.minshow = currentPath.minshow ?? 0;
      currentPath.maxshow = currentPath.maxshow ?? 1;
      currentPath.normalize = currentPath.normalize ?? false;
      const normalizeDataValue = currentPath.normalize
        ? 1
        : normalizeData[i];
      if (
        currentPath.minshow <= normalizeData[i] &&
        currentPath.maxshow >= normalizeData[i]
      ) {
        switch (currentPath.d) {
          // LineTo Commands
          case "L": {
            const angleStart =
              (deg * (i + currentPath.sdeg / 100) - fixOrientation) * pi180;
            const angleEnd =
              (deg * (i + currentPath.edeg / 100) - fixOrientation) * pi180;

            const pos_x =
              left +
              (length *
                (currentPath.sr / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.cos(angleStart);
            const pos_y =
              top +
              (length *
                (currentPath.sr / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.sin(angleStart);

            const end_pos_x =
              left +
              (length *
                (currentPath.er / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.cos(angleEnd);
            const end_pos_y =
              top +
              (length *
                (currentPath.er / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.sin(angleEnd);

            if (pos_x !== last_pos_x || pos_y !== last_pos_y) {
              path += `M ${pos_x} ${pos_y} `;
            }

            path += `L ${end_pos_x} ${end_pos_y} `;

            last_pos_x = end_pos_x;
            last_pos_y = end_pos_y;
            break;
          }

          // Cubic Bézier Curve Commands
          case "C": {
            const angleStart =
              (deg * (i + currentPath.sdeg / 100) - fixOrientation) * pi180;
            const angle =
              (deg * (i + currentPath.deg / 100) - fixOrientation) * pi180;
            const angleEnd =
              (deg * (i + currentPath.edeg / 100) - fixOrientation) * pi180;

            const pos_x =
              left +
              (length *
                (currentPath.sr / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.cos(angleStart);
            const pos_y =
              top +
              (length *
                (currentPath.sr / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.sin(angleStart);

            const center_pos_x =
              left +
              (length *
                (currentPath.r / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.cos(angle);
            const center_pos_y =
              top +
              (length *
                (currentPath.r / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.sin(angle);

            const end_pos_x =
              left +
              (length *
                (currentPath.er / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.cos(angleEnd);
            const end_pos_y =
              top +
              (length *
                (currentPath.er / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.sin(angleEnd);

            if (pos_x !== last_pos_x || pos_y !== last_pos_y) {
              path += `M ${pos_x} ${pos_y} `;
            }

            path += `C ${pos_x} ${pos_y} ${center_pos_x} ${center_pos_y} ${end_pos_x} ${end_pos_y} `;

            last_pos_x = end_pos_x;
            last_pos_y = end_pos_y;
            break;
          }

          // Quadratic Bézier Curve Commands
          case "Q": {
            const angleStart =
              (deg * (i + currentPath.sdeg / 100) - fixOrientation) * pi180;
            const angle =
              (deg * (i + currentPath.deg / 100) - fixOrientation) * pi180;
            const angleEnd =
              (deg * (i + currentPath.edeg / 100) - fixOrientation) * pi180;

            const pos_x =
              left +
              (length *
                (currentPath.sr / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.cos(angleStart);
            const pos_y =
              top +
              (length *
                (currentPath.sr / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.sin(angleStart);

            const center_pos_x =
              left +
              (length *
                (currentPath.r / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.cos(angle);
            const center_pos_y =
              top +
              (length *
                (currentPath.r / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.sin(angle);

            const end_pos_x =
              left +
              (length *
                (currentPath.er / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.cos(angleEnd);
            const end_pos_y =
              top +
              (length *
                (currentPath.er / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.sin(angleEnd);

            if (pos_x !== last_pos_x || pos_y !== last_pos_y) {
              path += `M ${pos_x} ${pos_y} `;
            }

            path += `Q ${center_pos_x} ${center_pos_y} ${end_pos_x} ${end_pos_y} `;

            last_pos_x = end_pos_x;
            last_pos_y = end_pos_y;
            break;
          }

          // Elliptical Arc Curve Commands
          case "A": {
            const angleStart =
              (deg * (i + currentPath.sdeg / 100) - fixOrientation) * pi180;
            const angleEnd =
              (deg * (i + currentPath.edeg / 100) - fixOrientation) * pi180;

            const pos_x =
              left +
              (length *
                (currentPath.sr / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.cos(angleStart);
            const pos_y =
              top +
              (length *
                (currentPath.sr / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.sin(angleStart);

            const end_pos_x =
              left +
              (length *
                (currentPath.er / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.cos(angleEnd);
            const end_pos_y =
              top +
              (length *
                (currentPath.er / 100) *
                normalizeDataValue *
                positive *
                mirror *
                invert +
                distance) *
              Math.sin(angleEnd);

            if (pos_x !== last_pos_x || pos_y !== last_pos_y) {
              path += `M ${pos_x} ${pos_y} `;
            }

            const angle = (deg * i * currentPath.angle) / 100;
            const rx = (currentPath.rx * deg) / 100;
            const ry = (currentPath.ry * deg) / 100;

            let { sweep } = currentPath;
            if (positive == -1) {
              if (sweep == 1) {
                sweep = 0;
              } else {
                sweep = 1;
              }
            }
            if (mirror == -1) {
              if (sweep == 1) {
                sweep = 0;
              } else {
                sweep = 1;
              }
            }
            path += `A ${rx} ${ry} ${angle} ${currentPath.arc} ${sweep} ${end_pos_x} ${end_pos_y} `;

            last_pos_x = end_pos_x;
            last_pos_y = end_pos_y;
            break;
          }

          // ClosePath Commands
          case "Z":
            path += "Z ";
            break;

          default:
            break;
        }
      }
    }
  }
  return path;
}