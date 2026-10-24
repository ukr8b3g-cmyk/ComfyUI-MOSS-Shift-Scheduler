import { app } from "../../scripts/app.js";

const modes = {
    "Radiance Shift (Compatible)": "MOSS Shift Scheduler",
    "MOSS Standard": "MOSS Curve Scheduler",
    "MOSS DMD": "MOSS Sigma Scheduler",
    "Balanced": "MOSS Shift Scheduler",
    "Power": "MOSS Curve Scheduler",
    "Offset": "MOSS Sigma Scheduler",
    "moss_shift_balanced": "MOSS Shift Scheduler",
    "moss_shift_power": "MOSS Curve Scheduler",
    "moss_shift_offset": "MOSS Sigma Scheduler",
};
const schedulers = {
    moss_radiance_shift: "MOSS Shift Scheduler",
    moss_standard: "MOSS Curve Scheduler",
    moss_dmd: "MOSS Sigma Scheduler",
    moss_shift_balanced: "MOSS Shift Scheduler",
    moss_shift_power: "MOSS Curve Scheduler",
    moss_shift_offset: "MOSS Sigma Scheduler",
};
const coreNodes = new Set(["KSampler", "KSamplerAdvanced", "BasicScheduler"]);

function migrate(graph) {
    for (const node of graph.nodes ?? []) {
        const names = node.type === "MOSS_Scheduler" ? modes : coreNodes.has(node.type) ? schedulers : null;
        if (names && Array.isArray(node.widgets_values)) {
            node.widgets_values = node.widgets_values.map(value =>
                typeof value === "string" && Object.hasOwn(names, value) ? names[value] : value
            );
        }
        if (node.type === "MOSS_Scheduler" && node.title === "MOSS Scheduler") {
            node.title = "MOSS Shift Scheduler";
        }
    }
    for (const subgraph of graph.definitions?.subgraphs ?? []) {
        migrate(subgraph);
    }
}

app.registerExtension({
    name: "MOSS.ShiftScheduler.Rename",
    beforeConfigureGraph(graphData) {
        migrate(graphData);
    },
});
