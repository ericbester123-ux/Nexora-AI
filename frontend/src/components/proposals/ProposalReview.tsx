"use client";

import { useState } from "react";
import { proposalService } from "@/services/proposal.service";
import { useProposals } from "@/hooks/useProposals";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { ErrorState } from "@/components/shared/ErrorState";
import { useToast } from "@/components/ui/toaster";
import {
  CheckCircle2, XCircle, Save, Send, FileEdit, Eye, History, MessageSquare,
} from "lucide-react";
import type { Proposal, ReadinessResponse, ProposalVersion, EvaluationResponse, ImproveResponse } from "@/types/proposal";

const IMPROVEMENT_STYLES = [
  { value: "shorter", label: "Shorter" },
  { value: "longer", label: "Longer" },
  { value: "more_technical", label: "More Technical" },
  { value: "less_technical", label: "Less Technical" },
  { value: "more_persuasive", label: "More Persuasive" },
  { value: "formal", label: "Formal" },
  { value: "casual", label: "Casual" },
];

interface ProposalReviewProps {
  proposal: Proposal;
  id: string;
}

export function ProposalReview({ proposal, id }: ProposalReviewProps) {
  const {
    review, markReady, markSubmitted, archive, readiness, edit, versions, notes,
    improve, evaluate, requestApproval, approve: approveAction, reject: rejectAction, queue,
  } = useProposals();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState("review");
  const [coverLetter, setCoverLetter] = useState(proposal.cover_letter || "");
  const [bidAmount, setBidAmount] = useState(proposal.bid_amount?.toString() || "");
  const [duration, setDuration] = useState(proposal.estimated_duration || "");
  const [changeSummary, setChangeSummary] = useState("");
  const [noteContent, setNoteContent] = useState("");

  const [improveStyle, setImproveStyle] = useState("shorter");
  const [customInstruction, setCustomInstruction] = useState("");
  const [focusSection, setFocusSection] = useState("");
  const [evaluationResult, setEvaluationResult] = useState<EvaluationResponse | null>(null);
  const [improveResult, setImproveResult] = useState<ImproveResponse | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const { data: readinessData, isLoading: readinessLoading } = readiness(id);
  const { data: versionsData } = versions(id);
  const { data: notesData, refetch: refetchNotes } = notes(id);

  const handleReview = async () => {
    try { await review.mutateAsync(id); toast({ title: "Moved to Under Review", variant: "success" }); }
    catch { toast({ title: "Failed to review", variant: "destructive" }); }
  };

  const handleReady = async () => {
    try { await markReady.mutateAsync(id); toast({ title: "Marked as Ready to Submit", variant: "success" }); }
    catch { toast({ title: "Readiness check failed", variant: "destructive" }); }
  };

  const handleSubmit = async () => {
    try { await markSubmitted.mutateAsync(id); toast({ title: "Marked as Submitted", variant: "success" }); }
    catch { toast({ title: "Failed to submit", variant: "destructive" }); }
  };

  const handleArchive = async () => {
    try { await archive.mutateAsync(id); toast({ title: "Proposal archived", variant: "success" }); }
    catch { toast({ title: "Failed to archive", variant: "destructive" }); }
  };

  const handleSaveEdit = async () => {
    try {
      await edit.mutateAsync({ id, data: { cover_letter: coverLetter, bid_amount: bidAmount ? parseFloat(bidAmount) : undefined, estimated_duration: duration, change_summary: changeSummary } });
      toast({ title: "Proposal updated", variant: "success" });
    } catch {
      toast({ title: "Failed to save", variant: "destructive" });
    }
  };

  const handleAddNote = async () => {
    if (!noteContent.trim()) return;
    try {
      await proposalService.createNote(id, noteContent);
      setNoteContent("");
      refetchNotes();
      toast({ title: "Note added", variant: "success" });
    } catch {
      toast({ title: "Failed to add note", variant: "destructive" });
    }
  };

  const handleImprove = async () => {
    try {
      const result = await improve.mutateAsync({
        id,
        data: {
          style: improveStyle,
          custom_instruction: improveStyle === "custom" ? customInstruction : undefined,
          focus_section: focusSection || undefined,
        },
      });
      setImproveResult(result);
      toast({ title: `Improvement applied (${improveStyle})`, variant: "success" });
    } catch {
      toast({ title: "Failed to improve proposal", variant: "destructive" });
    }
  };

  const handleEvaluate = async () => {
    try {
      const result = await evaluate.mutateAsync(id);
      setEvaluationResult(result);
      toast({ title: "Evaluation complete", variant: "success" });
    } catch {
      toast({ title: "Failed to evaluate", variant: "destructive" });
    }
  };

  const handleRequestApproval = async () => {
    try {
      await requestApproval.mutateAsync(id);
      toast({ title: "Sent for human approval", variant: "success" });
    } catch {
      toast({ title: "Failed to request approval", variant: "destructive" });
    }
  };

  const handleApprove = async () => {
    try {
      await approveAction.mutateAsync(id);
      toast({ title: "Proposal approved", variant: "success" });
    } catch {
      toast({ title: "Failed to approve", variant: "destructive" });
    }
  };

  const handleReject = async () => {
    try {
      await rejectAction.mutateAsync({ id, reason: rejectReason || undefined });
      toast({ title: "Proposal rejected", variant: "success" });
    } catch {
      toast({ title: "Failed to reject", variant: "destructive" });
    }
  };

  const handleQueue = async () => {
    try {
      await queue.mutateAsync(id);
      toast({ title: "Proposal queued", variant: "success" });
    } catch {
      toast({ title: "Failed to queue", variant: "destructive" });
    }
  };

  const isAiGenerated = proposal.status === "ai_generated";
  const isAwaitingApproval = proposal.status === "awaiting_approval";
  const isApproved = proposal.status === "approved";
  const isRejected = proposal.status === "rejected";
  const isQueued = proposal.status === "queued";

  const scoreColor = proposal.ai_evaluation_score
    ? proposal.ai_evaluation_score >= 0.8 ? "text-emerald-500"
      : proposal.ai_evaluation_score >= 0.5 ? "text-amber-500"
      : "text-destructive"
    : "text-muted-foreground";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{proposal.title || "Proposal Review"}</h2>
          <p className="text-muted-foreground">Review and manage your proposal</p>
        </div>
        <div className="flex items-center gap-2">
          {proposal.status === "draft" && <Button onClick={handleReview}><Send className="mr-2 h-4 w-4" /> Send for Review</Button>}
          {isAiGenerated && <Button onClick={handleRequestApproval}><CheckCircle2 className="mr-2 h-4 w-4" /> Request Approval</Button>}
          {isAwaitingApproval && <Button onClick={handleApprove}><CheckCircle2 className="mr-2 h-4 w-4" /> Approve</Button>}
          {isAwaitingApproval && <Button variant="destructive" onClick={handleReject}><XCircle className="mr-2 h-4 w-4" /> Reject</Button>}
          {isApproved && <Button onClick={handleQueue}><Send className="mr-2 h-4 w-4" /> Queue</Button>}
          {isApproved && <Button onClick={handleReady}><CheckCircle2 className="mr-2 h-4 w-4" /> Mark Ready</Button>}
          {isQueued && <Button onClick={handleSubmit}><Send className="mr-2 h-4 w-4" /> Submit</Button>}
          {proposal.status === "under_review" && <Button onClick={handleReady}><CheckCircle2 className="mr-2 h-4 w-4" /> Mark Ready</Button>}
          {proposal.status === "ready_to_submit" && <Button onClick={handleSubmit}><Send className="mr-2 h-4 w-4" /> Submit</Button>}
          <Button variant="outline" onClick={handleArchive}><XCircle className="mr-2 h-4 w-4" /> Archive</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Status</CardTitle></CardHeader>
          <CardContent><Badge variant="default" className="capitalize">{proposal.status.replace("_", " ")}</Badge></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Bid Amount</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{proposal.bid_amount ? `$${proposal.bid_amount.toLocaleString()}` : "—"}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">AI Score</CardTitle></CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <span className={`text-2xl font-bold ${scoreColor}`}>{proposal.ai_evaluation_score ? `${Math.round(proposal.ai_evaluation_score * 100)}%` : proposal.ai_score ? `${proposal.ai_score}%` : "—"}</span>
              {(proposal.ai_evaluation_score || proposal.ai_score) && (
                <Progress value={(proposal.ai_evaluation_score || proposal.ai_score || 0) * 100} className="flex-1" />
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="flex-wrap">
          <TabsTrigger value="review"><Eye className="mr-2 h-4 w-4" /> Review</TabsTrigger>
          <TabsTrigger value="edit"><FileEdit className="mr-2 h-4 w-4" /> Edit</TabsTrigger>
          <TabsTrigger value="improve"><Send className="mr-2 h-4 w-4" /> AI Improve</TabsTrigger>
          <TabsTrigger value="evaluate"><CheckCircle2 className="mr-2 h-4 w-4" /> AI Evaluate</TabsTrigger>
          <TabsTrigger value="readiness"><CheckCircle2 className="mr-2 h-4 w-4" /> Readiness</TabsTrigger>
          <TabsTrigger value="history"><History className="mr-2 h-4 w-4" /> History</TabsTrigger>
          <TabsTrigger value="notes"><MessageSquare className="mr-2 h-4 w-4" /> Notes</TabsTrigger>
        </TabsList>

        <TabsContent value="review" className="space-y-4 mt-4">
          <Card>
            <CardContent className="pt-6">
              <h3 className="font-semibold mb-2">Cover Letter</h3>
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">{proposal.cover_letter || "No cover letter yet."}</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="edit" className="space-y-4 mt-4">
          <Card>
            <CardContent className="pt-6 space-y-4">
              <div className="space-y-2">
                <Label>Cover Letter</Label>
                <Textarea
                  value={coverLetter}
                  onChange={(e) => setCoverLetter(e.target.value)}
                  rows={10}
                  className="font-mono text-sm"
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Bid Amount ($)</Label>
                  <Input type="number" value={bidAmount} onChange={(e) => setBidAmount(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>Estimated Duration</Label>
                  <Input value={duration} onChange={(e) => setDuration(e.target.value)} placeholder="e.g., 2 weeks" />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Change Summary</Label>
                <Input value={changeSummary} onChange={(e) => setChangeSummary(e.target.value)} placeholder="What changed in this edit?" />
              </div>
              <Button onClick={handleSaveEdit} disabled={edit.isPending}>
                <Save className="mr-2 h-4 w-4" /> {edit.isPending ? "Saving..." : "Save Changes"}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="improve" className="space-y-4 mt-4">
          <Card>
            <CardContent className="pt-6 space-y-4">
              <div>
                <h3 className="font-semibold mb-1">AI Improvement</h3>
                <p className="text-sm text-muted-foreground">Select a style to regenerate your proposal</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {IMPROVEMENT_STYLES.map((s) => (
                  <Button
                    key={s.value}
                    variant={improveStyle === s.value ? "default" : "outline"}
                    size="sm"
                    onClick={() => setImproveStyle(s.value)}
                  >
                    {s.label}
                  </Button>
                ))}
              </div>
              {improveStyle === "custom" && (
                <div className="space-y-2">
                  <Label>Custom Instruction</Label>
                  <Textarea
                    value={customInstruction}
                    onChange={(e) => setCustomInstruction(e.target.value)}
                    placeholder="Describe how you want the proposal improved..."
                    rows={3}
                  />
                </div>
              )}
              <div className="space-y-2">
                <Label>Focus Section (optional)</Label>
                <Input
                  value={focusSection}
                  onChange={(e) => setFocusSection(e.target.value)}
                  placeholder="e.g., coverLetter, executiveSummary"
                />
              </div>
              <Button onClick={handleImprove} disabled={improve.isPending}>
                <Send className="mr-2 h-4 w-4" /> {improve.isPending ? "Improving..." : "Improve"}
              </Button>
              {improveResult && (
                <div className="rounded-lg border p-4 mt-2">
                  <p className="text-sm font-medium mb-1">Improvement Result</p>
                  <p className="text-xs text-muted-foreground">
                    Version {improveResult.version_number} created with style: {improveResult.style}
                  </p>
                  {improveResult.cover_letter && (
                    <div className="mt-2">
                      <p className="text-xs font-medium mb-1">New Cover Letter Preview:</p>
                      <p className="text-xs text-muted-foreground line-clamp-3">{improveResult.cover_letter}</p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="evaluate" className="space-y-4 mt-4">
          <Card>
            <CardContent className="pt-6 space-y-4">
              <div>
                <h3 className="font-semibold mb-1">AI Evaluation</h3>
                <p className="text-sm text-muted-foreground">Get detailed quality scores and feedback</p>
              </div>
              <Button onClick={handleEvaluate} disabled={evaluate.isPending}>
                <CheckCircle2 className="mr-2 h-4 w-4" /> {evaluate.isPending ? "Evaluating..." : "Evaluate"}
              </Button>
              {evaluationResult && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {[
                      { key: "overall_score", label: "Overall" },
                      { key: "completeness_score", label: "Completeness" },
                      { key: "persuasiveness_score", label: "Persuasiveness" },
                      { key: "relevance_score", label: "Relevance" },
                      { key: "clarity_score", label: "Clarity" },
                      { key: "formatting_score", label: "Formatting" },
                    ].map(({ key, label }) => {
                      const val = evaluationResult.scores[key as keyof typeof evaluationResult.scores] as number;
                      return (
                        <div key={key} className="rounded-lg border p-3 text-center">
                          <p className="text-xs text-muted-foreground">{label}</p>
                          <p className={`text-xl font-bold ${val >= 0.8 ? "text-emerald-500" : val >= 0.5 ? "text-amber-500" : "text-destructive"}`}>
                            {Math.round(val * 100)}%
                          </p>
                        </div>
                      );
                    })}
                  </div>
                  {evaluationResult.scores.strengths.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-emerald-600 mb-1">Strengths</p>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        {evaluationResult.scores.strengths.map((s, i) => (
                          <li key={i} className="flex items-start gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-500 mt-0.5 shrink-0" />{s}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {evaluationResult.scores.weaknesses.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-destructive mb-1">Weaknesses</p>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        {evaluationResult.scores.weaknesses.map((w, i) => (
                          <li key={i} className="flex items-start gap-2"><XCircle className="h-4 w-4 text-destructive mt-0.5 shrink-0" />{w}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {evaluationResult.scores.suggestions.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-blue-600 mb-1">Suggestions</p>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        {evaluationResult.scores.suggestions.map((s, i) => (
                          <li key={i} className="flex items-start gap-2"><CheckCircle2 className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />{s}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="readiness" className="space-y-4 mt-4">
          <Card>
            <CardContent className="pt-6">
              {readinessLoading ? <LoadingSpinner /> : readinessData ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-semibold">Readiness: </span>
                    <Badge variant={readinessData.ready ? "success" : "destructive"}>
                      {readinessData.ready ? "Ready to Submit" : "Not Ready"}
                    </Badge>
                  </div>
                  <Separator />
                  {readinessData.checks.map((check) => (
                    <div key={check.field} className="flex items-center justify-between rounded-lg border p-3">
                      <span className="text-sm capitalize">{check.field.replace("_", " ")}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">{check.message}</span>
                        {check.status === "pass"
                          ? <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                          : <XCircle className="h-5 w-5 text-destructive" />}
                      </div>
                    </div>
                  ))}
                  {proposal.status === "awaiting_approval" && (
                    <div className="flex gap-2 pt-2">
                      <Button onClick={handleApprove}><CheckCircle2 className="mr-2 h-4 w-4" /> Approve</Button>
                      <Button variant="destructive" onClick={handleReject}><XCircle className="mr-2 h-4 w-4" /> Reject</Button>
                    </div>
                  )}
                  {proposal.status === "rejected" && (
                    <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-3">
                      <p className="text-sm font-medium text-destructive">Rejected</p>
                      {proposal.rejection_reason && <p className="text-xs text-muted-foreground mt-1">{proposal.rejection_reason}</p>}
                    </div>
                  )}
                </div>
              ) : <p className="text-muted-foreground">Unable to check readiness.</p>}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="space-y-4 mt-4">
          <Card>
            <CardContent className="pt-6">
              {versionsData?.items?.length ? (
                <div className="space-y-3">
                  {versionsData.items.map((v: ProposalVersion) => (
                    <div key={v.id} className="flex items-center justify-between rounded-lg border p-3">
                      <div>
                        <p className="text-sm font-medium">Version {v.version_number}</p>
                        <p className="text-xs text-muted-foreground">{v.change_summary || "No summary"} · {new Date(v.created_at).toLocaleDateString()}</p>
                      </div>
                      <Badge variant="secondary">v{v.version_number}</Badge>
                    </div>
                  ))}
                </div>
              ) : <p className="text-muted-foreground">No version history yet.</p>}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notes" className="space-y-4 mt-4">
          <Card>
            <CardContent className="pt-6 space-y-4">
              <div className="flex gap-2">
                <Input value={noteContent} onChange={(e) => setNoteContent(e.target.value)} placeholder="Add a private note..." />
                <Button onClick={handleAddNote} disabled={!noteContent.trim()}>Add</Button>
              </div>
              {notesData?.items?.length ? (
                <div className="space-y-2">
                  {notesData.items.map((note) => (
                    <div key={note.id} className="rounded-lg border p-3">
                      <p className="text-sm">{note.content}</p>
                      <p className="text-xs text-muted-foreground mt-1">{new Date(note.created_at).toLocaleString()}</p>
                    </div>
                  ))}
                </div>
              ) : <p className="text-sm text-muted-foreground">No notes yet.</p>}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {proposal.status === "awaiting_approval" && (
        <Card className="border-amber-200 bg-amber-50 dark:bg-amber-950/20">
          <CardContent className="pt-6 flex items-center justify-between">
            <div>
              <p className="font-semibold text-amber-800 dark:text-amber-300">Awaiting Your Approval</p>
              <p className="text-sm text-amber-600 dark:text-amber-400">This AI-generated proposal needs your review before it can be submitted.</p>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleApprove}><CheckCircle2 className="mr-2 h-4 w-4" /> Approve</Button>
              <Button variant="destructive" onClick={handleReject}><XCircle className="mr-2 h-4 w-4" /> Reject</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {proposal.status === "rejected" && proposal.rejection_reason && (
        <Card className="border-destructive/20">
          <CardContent className="pt-6">
            <p className="text-sm font-medium text-destructive">Rejection Reason</p>
            <p className="text-sm text-muted-foreground mt-1">{proposal.rejection_reason}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
