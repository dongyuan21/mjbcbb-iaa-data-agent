#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const [inputPath, pngPath, svgPath] = process.argv.slice(2);
if (!inputPath || !pngPath) {
  throw new Error("用法: 渲染Excalidraw.mjs <input.excalidraw> <output.png> [output.svg]");
}

const require = createRequire(import.meta.url);
const sharp = require("sharp");

const document = JSON.parse(fs.readFileSync(inputPath, "utf8"));
const elements = (document.elements || []).filter((element) => !element.isDeleted);
const unsupported = [...new Set(elements
  .map((element) => element.type)
  .filter((type) => !["rectangle", "ellipse", "diamond", "line", "arrow", "text", "freedraw", "frame"].includes(type)))];
if (unsupported.length) {
  throw new Error(`存在不支持的 Excalidraw 元素，拒绝降级导出: ${unsupported.join(", ")}`);
}

const escapeXml = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&apos;");

const bounds = elements.reduce((acc, element) => {
  const points = Array.isArray(element.points) ? element.points : [];
  const xs = [element.x || 0, (element.x || 0) + (element.width || 0), ...points.map((point) => (element.x || 0) + point[0])];
  const ys = [element.y || 0, (element.y || 0) + (element.height || 0), ...points.map((point) => (element.y || 0) + point[1])];
  return {
    minX: Math.min(acc.minX, ...xs), minY: Math.min(acc.minY, ...ys),
    maxX: Math.max(acc.maxX, ...xs), maxY: Math.max(acc.maxY, ...ys)
  };
}, { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity });

if (!Number.isFinite(bounds.minX)) throw new Error("Excalidraw 文件没有可导出的元素");
const padding = 32;
const width = Math.max(1, Math.ceil(bounds.maxX - bounds.minX + padding * 2));
const height = Math.max(1, Math.ceil(bounds.maxY - bounds.minY + padding * 2));
const offsetX = -bounds.minX + padding;
const offsetY = -bounds.minY + padding;
const background = document.appState?.viewBackgroundColor || "#ffffff";

const strokeDash = (element) => element.strokeStyle === "dashed" ? "8 6" : element.strokeStyle === "dotted" ? "2 5" : "";
const rotation = (element) => {
  if (!element.angle) return "";
  const cx = (element.x || 0) + (element.width || 0) / 2 + offsetX;
  const cy = (element.y || 0) + (element.height || 0) / 2 + offsetY;
  return ` transform="rotate(${element.angle * 180 / Math.PI} ${cx} ${cy})"`;
};
const style = (element) => {
  const fill = element.backgroundColor && element.backgroundColor !== "transparent" ? element.backgroundColor : "none";
  const dash = strokeDash(element);
  return `fill="${escapeXml(fill)}" stroke="${escapeXml(element.strokeColor || "#1b1b1f")}" stroke-width="${element.strokeWidth || 1}"${dash ? ` stroke-dasharray="${dash}"` : ""} opacity="${(element.opacity ?? 100) / 100}"`;
};

const renderElement = (element) => {
  const x = (element.x || 0) + offsetX;
  const y = (element.y || 0) + offsetY;
  const w = element.width || 0;
  const h = element.height || 0;
  const rotate = rotation(element);
  if (element.type === "rectangle" || element.type === "frame") {
    const radius = element.roundness ? Math.min(12, w / 8, h / 8) : 0;
    return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${radius}" ${style(element)}${rotate}/>`;
  }
  if (element.type === "ellipse") {
    return `<ellipse cx="${x + w / 2}" cy="${y + h / 2}" rx="${w / 2}" ry="${h / 2}" ${style(element)}${rotate}/>`;
  }
  if (element.type === "diamond") {
    const points = `${x + w / 2},${y} ${x + w},${y + h / 2} ${x + w / 2},${y + h} ${x},${y + h / 2}`;
    return `<polygon points="${points}" ${style(element)}${rotate}/>`;
  }
  if (["line", "arrow", "freedraw"].includes(element.type)) {
    const points = (element.points || []).map((point) => `${x + point[0]},${y + point[1]}`).join(" ");
    const marker = element.type === "arrow" && element.endArrowhead !== null ? ' marker-end="url(#arrowhead)"' : "";
    return `<polyline points="${points}" fill="none" stroke="${escapeXml(element.strokeColor || "#1b1b1f")}" stroke-width="${element.strokeWidth || 1}" stroke-linecap="round" stroke-linejoin="round"${marker}${rotate}/>`;
  }
  if (element.type === "text") {
    const fontSize = element.fontSize || 20;
    const lineHeight = fontSize * (element.lineHeight || 1.25);
    const align = element.textAlign === "center" ? "middle" : element.textAlign === "right" ? "end" : "start";
    const textX = align === "middle" ? x + w / 2 : align === "end" ? x + w : x;
    const lines = String(element.text || element.originalText || "").split("\n");
    const tspans = lines.map((line, index) => `<tspan x="${textX}" dy="${index === 0 ? 0 : lineHeight}">${escapeXml(line)}</tspan>`).join("");
    return `<text x="${textX}" y="${y + fontSize}" text-anchor="${align}" fill="${escapeXml(element.strokeColor || "#1b1b1f")}" font-family="Arial, PingFang SC, sans-serif" font-size="${fontSize}" font-weight="${element.fontFamily === 1 ? 600 : 400}" opacity="${(element.opacity ?? 100) / 100}"${rotate}>${tspans}</text>`;
  }
  return "";
};

const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <defs><marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#1b1b1f"/></marker></defs>
  <rect width="100%" height="100%" fill="${escapeXml(background)}"/>
  ${elements.map(renderElement).join("\n  ")}
</svg>`;

fs.mkdirSync(path.dirname(pngPath), { recursive: true });
if (svgPath) {
  fs.mkdirSync(path.dirname(svgPath), { recursive: true });
  fs.writeFileSync(svgPath, svg, "utf8");
}
await sharp(Buffer.from(svg)).png().toFile(pngPath);
process.stdout.write(JSON.stringify({ width, height, elementCount: elements.length }));
