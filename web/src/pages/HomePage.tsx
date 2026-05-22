import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Activity,
  Bot,
  Cpu,
  DollarSign,
  History,
  MessageSquare,
  Plus,
  Settings,
  Terminal,
  TrendingUp,
} from "lucide-react";
import { api } from "@/lib/api";
import type {
  DashboardStatsResponse,
  RecentActivitySession,
  RecentActivityResponse,
} from "@/lib/api";
import { timeAgo } from "@/lib/utils";
import { Button } from "@kyssta/ui/ui/components/button";
import { Spinner } from "@kyssta/ui/ui/components/spinner";
import { Stats } from "@kyssta/ui/ui/components/stats";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Typography } from "@/components/NouiTypography";
import { usePageHeader } from "@/contexts/usePageHeader";
import { useI18n } from "@/i18n";

function formatTokens(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function formatCost(n: number): string {
  if (n >= 1) return `$${n.toFixed(2)}`;
  if (n >= 0.01) return `$${n.toFixed(4)}`;
  return `<$0.01`;
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  if (seconds < 86400) return `${(seconds / 3600).toFixed(1)}h`;
  return `${(seconds / 86400).toFixed(1)}d`;
}

function ModelBadge({ model }: { model: string | null }) {
  if (!model) return <span className="text-xs text-muted-foreground/50">—</span>;
  const short = model.split("/").pop() ?? model;
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-muted/30 px-2 py-0.5 text-[10px] text-muted-foreground/70">
      <Cpu className="h-2.5 w-2.5" />
      {short}
    </span>
  );
}

export default function HomePage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStatsResponse | null>(null);
  const [activity, setActivity] = useState<RecentActivitySession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsData, activityData] = await Promise.all([
        api.getDashboardStats(),
        api.getRecentActivity(8),
      ]);
      setStats(statsData);
      setActivity(activityData.sessions);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const refresh = useCallback(() => {
    load();
  }, [load]);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 pb-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
            <Activity className="h-4 w-4 text-primary" />
          </div>
          <div>
            <Typography className="text-sm font-bold tracking-wide text-midground">
              Dashboard
            </Typography>
            <Typography className="text-[10px] text-muted-foreground/50">
              {stats
                ? `${stats.total_sessions} sessions · ${formatTokens(stats.total_tokens)} tokens`
                : "Loading..."}
            </Typography>
          </div>
        </div>
        <Button ghost size="icon" onClick={refresh} disabled={loading} title="Refresh">
          <Spinner className={`h-3.5 w-3.5 ${loading ? "animate-spin" : "opacity-50 hover:opacity-100"}`} />
        </Button>
      </div>

      {loading && !stats && (
        <div className="flex flex-1 items-center justify-center">
          <Spinner className="text-xl text-primary" />
        </div>
      )}

      {error && (
        <Card>
          <CardContent className="py-6">
            <p className="text-center text-sm text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {stats && (
        <>
          {/* Quick actions */}
          <div className="flex gap-2">
            <Button
              onClick={() => navigate("/sessions")}
              className="flex items-center gap-2 text-xs"
            >
              <MessageSquare className="h-3.5 w-3.5" />
              Sessions
            </Button>
            <Button
              onClick={() => navigate("/analytics")}
              variant="outline"
              className="flex items-center gap-2 text-xs"
            >
              <TrendingUp className="h-3.5 w-3.5" />
              Analytics
            </Button>
            <Button
              onClick={() => navigate("/config")}
              variant="outline"
              className="flex items-center gap-2 text-xs"
            >
              <Settings className="h-3.5 w-3.5" />
              Config
            </Button>
          </div>

          {/* Stats cards */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardContent className="py-4">
                <Stats
                  items={[
                    {
                      label: "API Calls",
                      value: String(stats.total_api_calls),
                    },
                    {
                      label: "Today",
                      value: String(stats.today.api_calls),
                    },
                  ]}
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="py-4">
                <Stats
                  items={[
                    {
                      label: "Total Tokens",
                      value: formatTokens(stats.total_tokens),
                    },
                    {
                      label: "Input / Output",
                      value: `${formatTokens(stats.all_time.input_tokens)} / ${formatTokens(stats.all_time.output_tokens)}`,
                    },
                  ]}
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="py-4">
                <Stats
                  items={[
                    {
                      label: "Est. Cost",
                      value: formatCost(stats.all_time.estimated_cost),
                    },
                    {
                      label: "Sessions",
                      value: String(stats.total_sessions),
                    },
                  ]}
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="py-4">
                <Stats
                  items={[
                    {
                      label: "Active",
                      value: String(stats.active_sessions),
                    },
                    {
                      label: "Idle",
                      value: String(stats.idle_sessions),
                    },
                  ]}
                />
              </CardContent>
            </Card>
          </div>

          {/* Activity feed */}
          <div className="flex items-center gap-2 border-t border-current/10 pt-3">
            <History className="h-3.5 w-3.5 text-muted-foreground/50" />
            <Typography className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/50">
              Recent Sessions
            </Typography>
          </div>

          <div className="flex flex-col gap-1">
            {activity.length === 0 && (
              <div className="flex flex-col items-center py-12 text-muted-foreground/40">
                <MessageSquare className="mb-2 h-6 w-6" />
                <p className="text-xs">No sessions yet</p>
                <p className="mt-1 text-[10px]">Start a conversation to see activity here</p>
              </div>
            )}
            {activity.map((s) => (
              <button
                key={s.id}
                onClick={() => navigate(`/sessions`)}
                className="group flex items-center gap-3 rounded-lg border border-transparent px-3 py-2 text-left transition-colors hover:border-current/10 hover:bg-muted/20"
              >
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/5">
                  <Bot className="h-3 w-3 text-primary/60" />
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-xs font-medium text-midground/80">
                      {s.title || "Untitled Session"}
                    </span>
                    <ModelBadge model={s.model} />
                  </div>
                  <div className="mt-0.5 flex items-center gap-2 text-[10px] text-muted-foreground/50">
                    <span>{formatDuration(s.duration_seconds)}</span>
                    <span>·</span>
                    <span>{s.api_calls} calls</span>
                    <span>·</span>
                    <span>{formatTokens(s.total_tokens)} tokens</span>
                    {s.estimated_cost > 0 && (
                      <>
                        <span>·</span>
                        <span>{formatCost(s.estimated_cost)}</span>
                      </>
                    )}
                  </div>
                </div>

                <div className="shrink-0 text-[10px] text-muted-foreground/40">
                  {timeAgo(s.started_at)}
                </div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
