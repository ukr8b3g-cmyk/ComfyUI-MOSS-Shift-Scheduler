const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

let extension;
const source = fs.readFileSync(path.join(__dirname, "../web/rename.js"), "utf8")
    .replace('import { app } from "../../scripts/app.js";', "");
vm.runInNewContext(source, { app: { registerExtension(value) { extension = value; } } });
const graph = {
    nodes: [
        { type: "MOSS_Scheduler", title: "MOSS Scheduler", widgets_values: ["Radiance Shift (Compatible)", 25, 1] },
        { type: "MOSS_Scheduler", title: "My title", widgets_values: ["MOSS Standard", 8, 0.5] },
        { type: "MOSS_Scheduler", widgets_values: ["MOSS DMD", 20, 1] },
        { type: "KSampler", widgets_values: [123, "fixed", 25, 2.5, "er_sde", "moss_standard", 1] },
        { type: "KSamplerAdvanced", widgets_values: ["moss_dmd", 25] },
        { type: "BasicScheduler", widgets_values: ["moss_radiance_shift", 25, 1] },
        { type: "CLIPTextEncode", widgets_values: ["moss_dmd"] },
    ],
    definitions: { subgraphs: [{ nodes: [{ type: "MOSS_Scheduler", widgets_values: ["MOSS Standard", 25, 1] }] }] },
};
extension.beforeConfigureGraph(graph);
assert.deepEqual(graph.nodes[0].widgets_values, ["MOSS Shift Scheduler", 25, 1]);
assert.equal(graph.nodes[0].title, "MOSS Shift Scheduler");
assert.deepEqual(graph.nodes[1].widgets_values, ["MOSS Curve Scheduler", 8, 0.5]);
assert.equal(graph.nodes[1].title, "My title");
assert.deepEqual(graph.nodes[2].widgets_values, ["MOSS Sigma Scheduler", 20, 1]);
assert.deepEqual(graph.nodes[3].widgets_values, [123, "fixed", 25, 2.5, "er_sde", "MOSS Curve Scheduler", 1]);
assert.deepEqual(graph.nodes[4].widgets_values, ["MOSS Sigma Scheduler", 25]);
assert.deepEqual(graph.nodes[5].widgets_values, ["MOSS Shift Scheduler", 25, 1]);
assert.deepEqual(graph.nodes[6].widgets_values, ["moss_dmd"]);
assert.equal(graph.definitions.subgraphs[0].nodes[0].widgets_values[0], "MOSS Curve Scheduler");
const recent = {nodes: [
    {type: "MOSS_Scheduler", widgets_values: ["Balanced", 25, 1]},
    {type: "MOSS_Scheduler", widgets_values: ["Power", 25, 1]},
    {type: "MOSS_Scheduler", widgets_values: ["Offset", 25, 1]},
    {type: "KSampler", widgets_values: ["moss_shift_balanced"]},
    {type: "KSampler", widgets_values: ["moss_shift_power"]},
    {type: "KSampler", widgets_values: ["moss_shift_offset"]},
]};
extension.beforeConfigureGraph(recent);
assert.deepEqual(recent.nodes.map(n => n.widgets_values[0]), [
    "MOSS Shift Scheduler", "MOSS Curve Scheduler", "MOSS Sigma Scheduler",
    "MOSS Shift Scheduler", "MOSS Curve Scheduler", "MOSS Sigma Scheduler",
]);
const migrated = JSON.stringify(graph);
extension.beforeConfigureGraph(graph);
assert.equal(JSON.stringify(graph), migrated);
console.log("PASS: old mode/core names migrate, custom titles/prompts/settings survive, repeat migration is unchanged");
