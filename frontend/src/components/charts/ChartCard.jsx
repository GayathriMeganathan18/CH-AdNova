import { useEffect, useRef, useState } from "react";
import ReactECharts from "echarts-for-react";
import { Maximize2, X, RefreshCw, ImageDown, FileSpreadsheet } from "lucide-react";
import { useChartTheme } from "./theme.js";
import { downloadCsv, slugify, triggerDownload } from "./chartUtils.js";

function ToolbarButton({ icon: Icon, label, onClick, disabled }) {
  return (
    <button
      type="button"
      title={label}
      aria-label={label}
      onClick={onClick}
      disabled={disabled}
      className="p-1.5 rounded-md text-ink3 hover:text-ink hover:bg-ink/10 transition-colors duration-150 disabled:opacity-40 disabled:pointer-events-none"
    >
      <Icon size={14} />
    </button>
  );
}

export default function ChartCard({ title, option, height = 240, onRefresh, csvData, headerExtra, className = "" }) {
  const [fullscreen, setFullscreen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const chartRef = useRef(null);
  const fsChartRef = useRef(null);
  const { colors } = useChartTheme();

  useEffect(() => {
    if (!fullscreen) return undefined;
    const onKey = (e) => {
      if (e.key === "Escape") setFullscreen(false);
    };
    window.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [fullscreen]);

  useEffect(() => {
    if (!fullscreen) return;
    const id = requestAnimationFrame(() => fsChartRef.current?.getEchartsInstance().resize());
    return () => cancelAnimationFrame(id);
  }, [fullscreen]);

  const handleRefresh = async () => {
    if (!onRefresh) return;
    setRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setRefreshing(false);
    }
  };

  const handleDownloadPng = (ref) => {
    const inst = ref.current?.getEchartsInstance();
    if (!inst) return;
    const url = inst.getDataURL({ type: "png", pixelRatio: 2, backgroundColor: colors.panel2 });
    triggerDownload(url, `${slugify(title)}.png`);
  };

  const handleDownloadCsv = () => {
    if (!csvData) return;
    downloadCsv(csvData, `${slugify(title)}.csv`);
  };

  return (
    <>
      <div className={`bg-panel2 shadow-card rounded-xl themed-transition duration-200 ${className}`}>
        <div className="flex items-center justify-between px-3 pt-2.5 pb-1 gap-2">
          <h3 className="text-sm font-semibold text-ink2 truncate">{title}</h3>
          <div className="chart-toolbar flex items-center gap-0.5 shrink-0">
            {headerExtra}
            {onRefresh && (
              <ToolbarButton
                icon={RefreshCw}
                label="Refresh"
                onClick={handleRefresh}
                disabled={refreshing}
              />
            )}
            <ToolbarButton icon={ImageDown} label="Download PNG" onClick={() => handleDownloadPng(chartRef)} />
            {csvData && <ToolbarButton icon={FileSpreadsheet} label="Download CSV" onClick={handleDownloadCsv} />}
            <ToolbarButton icon={Maximize2} label="Fullscreen" onClick={() => setFullscreen(true)} />
          </div>
        </div>
        <ReactECharts ref={chartRef} option={option} style={{ height }} notMerge lazyUpdate />
      </div>

      {fullscreen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 sm:p-8 transition-opacity duration-200"
          onClick={() => setFullscreen(false)}
          role="dialog"
          aria-modal="true"
          aria-label={title}
        >
          <div
            className="bg-panel2 border border-line rounded-xl w-full h-full max-w-6xl max-h-[88vh] flex flex-col shadow-2xl transition-transform duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-line shrink-0">
              <h3 className="text-sm font-semibold text-ink">{title}</h3>
              <div className="flex items-center gap-1">
                <ToolbarButton icon={ImageDown} label="Download PNG" onClick={() => handleDownloadPng(fsChartRef)} />
                {csvData && <ToolbarButton icon={FileSpreadsheet} label="Download CSV" onClick={handleDownloadCsv} />}
                <button
                  type="button"
                  aria-label="Close"
                  onClick={() => setFullscreen(false)}
                  className="p-1.5 rounded-md text-ink3 hover:text-ink hover:bg-ink/10 transition-colors duration-150 ml-1"
                >
                  <X size={18} />
                </button>
              </div>
            </div>
            <div className="flex-1 p-4 min-h-0">
              <ReactECharts ref={fsChartRef} option={option} style={{ height: "100%", width: "100%" }} notMerge lazyUpdate />
            </div>
          </div>
        </div>
      )}
    </>
  );
}
