"use client";

import React from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { labService } from "@/services/lab.service";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import {
  Clock,
  Sliders,
  BookOpen,
  ArrowLeft,
  ChevronRight,
  AlertCircle,
  HelpCircle,
  Terminal,
  Container,
  Layers,
  Cpu,
  Globe,
  Settings,
  GitBranch,
  Play,
  BarChart,
  Activity,
  HardDrive,
  CheckCircle2,
} from "lucide-react";
import Link from "next/link";

export default function LabDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  // Query lab detail
  const { data: lab, isLoading, error } = useQuery({
    queryKey: ["lab", slug],
    queryFn: () => labService.getLabBySlug(slug),
    retry: false,
  });

  // Dynamic Icon selector
  const getCategoryIcon = (cat: string) => {
    switch (cat.toLowerCase()) {
      case "linux":
        return <Terminal className="h-5 w-5 text-primary" />;
      case "docker":
        return <Container className="h-5 w-5 text-primary" />;
      case "kubernetes":
        return <Layers className="h-5 w-5 text-primary" />;
      case "terraform":
        return <Cpu className="h-5 w-5 text-primary" />;
      case "aws":
        return <Globe className="h-5 w-5 text-primary" />;
      case "azure":
        return <HardDrive className="h-5 w-5 text-primary" />;
      case "jenkins":
        return <Settings className="h-5 w-5 text-primary" />;
      case "ansible":
        return <BookOpen className="h-5 w-5 text-primary" />;
      case "git":
        return <GitBranch className="h-5 w-5 text-primary" />;
      case "github actions":
        return <Play className="h-5 w-5 text-primary" />;
      case "monitoring":
        return <BarChart className="h-5 w-5 text-primary" />;
      case "observability":
        return <Activity className="h-5 w-5 text-primary" />;
      default:
        return <HelpCircle className="h-5 w-5 text-primary" />;
    }
  };

  // Dynamic syllabus generator based on technology category
  const generateDynamicSyllabus = (cat: string, title: string) => {
    const defaultSyllabus = {
      prerequisites: [
        "Familiarity with basic DevOps terminology.",
        "A desktop web browser (Chrome, Firefox, or Safari).",
      ],
      objectives: [
        "Understand structural fundamentals of " + cat + ".",
        "Apply basic syntax configurations and verify logs.",
        "Perform diagnostics and identify configuration anomalies.",
      ],
      topics: [
        "Environment variables setup.",
        "Debugging and telemetry logs validation.",
        "Common configuration file architectures.",
      ],
    };

    switch (cat.toLowerCase()) {
      case "linux":
        return {
          prerequisites: [
            "Familiarity with file structures (folders/directories).",
            "Basic terminal commands concept.",
          ],
          objectives: [
            "Understand terminal commands structures and file paths.",
            "Manipulate user groups, chmod permissions, and files attributes.",
            "Combine operations utilizing redirection inputs and pipes.",
          ],
          topics: [
            "Directory Traversals (cd, ls, pwd)",
            "System permissions mapping (chmod, chown)",
            "Output pipeline redirection (>, >>, |)",
            "System processes inspection (ps, top)",
          ],
        };
      case "docker":
        return {
          prerequisites: [
            "Linux terminal interface familiarity.",
            "Understanding of IP addresses and ports mapping.",
          ],
          objectives: [
            "Execute and inspect containers runtimes in detached states.",
            "Mount local folder volumes to container targets.",
            "Author efficient Multi-stage Dockerfiles utilizing alpine runtimes.",
          ],
          topics: [
            "Container states management (run, stop, exec)",
            "Volumes and storage properties mapping (-v)",
            "Port exposures and adapter bindings (-p)",
            "Multi-stage Dockerfile configurations",
          ],
        };
      case "kubernetes":
        return {
          prerequisites: [
            "Docker runtimes and containers architecture.",
            "JSON/YAML configuration syntax parsing.",
          ],
          objectives: [
            "Declare pods specifications inside manifest sheets.",
            "Deploy highly-available apps scaled via Deployment controllers.",
            "Map internal ClusterIP endpoints to public Ingress adapters.",
          ],
          topics: [
            "YAML configuration declarations",
            "ReplicaSets and deployment rolling states",
            "Service endpoints bindings (NodePort, LoadBalancer)",
            "Volume mappings (PV and PVC bindings)",
          ],
        };
      case "terraform":
        return {
          prerequisites: [
            "Conceptual understanding of declarative programming.",
            "Familiarity with cloud resources concepts (Virtual Machines, Subnets).",
          ],
          objectives: [
            "Author declarative cloud infrastructure sheets utilizing HCL syntax.",
            "Validate state changes using preview operations (terraform plan).",
            "Establish local locks and organize state files.",
          ],
          topics: [
            "HCL declarations block formats",
            "Terraform initialization lifecycle (terraform init)",
            "Applying state blue prints (plan and apply)",
            "Local and Remote backend configurations",
          ],
        };
      case "aws":
        return {
          prerequisites: [
            "Familiarity with networks routing and client server connections.",
            "Basic understanding of command-line tools structures.",
          ],
          objectives: [
            "Configure administrative keys and manage secure user privileges using IAM.",
            "Orchestrate virtual compute resources and build secure VPC subnets.",
            "Deploy highly available object repositories and postgres database clusters.",
          ],
          topics: [
            "AWS Global Infrastructure Regions and Availability Zones",
            "Identity Access Management users, policies and scopes",
            "Elastic Compute Cloud virtual nodes provisionings",
            "VPC Classless Inter-Domain Routing boundaries",
          ],
        };
      case "ansible":
        return {
          prerequisites: [
            "Linux terminal interface familiarity.",
            "Basic understanding of YAML syntax layout.",
          ],
          objectives: [
            "Create push-based automation plays targeting inventory host groups.",
            "Write structured playbooks utilizing modules, handlers, and conditionals.",
            "Implement reusable system templates using Jinja2 syntax expressions.",
          ],
          topics: [
            "INI hosts inventory setups",
            "Playbooks execution using ansible-playbook",
            "Dynamic variables variables and fact gathering",
            "Modular scaling with Ansible Roles and Galaxy",
          ],
        };
      case "jenkins":
        return {
          prerequisites: [
            "Basic git repository flow concepts.",
            "General CI/CD automated deployment architectures.",
          ],
          objectives: [
            "Define declarative build-and-test stages using Jenkinsfiles.",
            "Configure log pruning best practices to optimize master node loads.",
            "Securely inject credentials and manage distributed build agents.",
          ],
          topics: [
            "Freestyle build jobs vs Pipeline as Code",
            "Jenkinsfile Declarative vs Scripted paradigm",
            "Credential store credential bindings",
            "Distributed builds and agent node labels",
          ],
        };
      case "git":
        return {
          prerequisites: [
            "Familiarity with text editors and directory structures.",
          ],
          objectives: [
            "Master staging area actions, commit history logs, and branch merges.",
            "Solve branching merge conflicts and recover deleted commits.",
            "Synchronize local changes with remote repositories and team workflows.",
          ],
          topics: [
            "Commit history graph navigations",
            "Branch pointers management and merging conflicts",
            "Advanced reflogs, stashes, and tags",
            "Remote sync commands (fetch, pull, push)",
          ],
        };
      case "github-actions":
        return {
          prerequisites: [
            "Basic git branching and repository setup.",
            "Familiarity with YAML structures.",
          ],
          objectives: [
            "Design event-triggered build workflows on the GitHub runner pools.",
            "Run testing suites and save artifacts using upload actions.",
            "Deploy secure release jobs utilizing environment secrets.",
          ],
          topics: [
            "Workflow execution triggers",
            "GitHub Actions Runner environments",
            "Build artifacts storage systems",
            "Runner Secrets security keys",
          ],
        };
      case "cicd":
        return {
          prerequisites: [
            "Basic Linux, Git, and containerization knowledge.",
          ],
          objectives: [
            "Build automated CI pipeline gates validating code checkins.",
            "Implement automated compilation, unit testing, and linting stages.",
            "Create repeatable continuous delivery deployment policies.",
          ],
          topics: [
            "Continuous Integration syntax verification",
            "Automated test suite executions",
            "Continuous Delivery release packaging",
            "Continuous Deployment rollbacks strategies",
          ],
        };
      default:
        return defaultSyllabus;
    }
  };

  // Loader state
  if (isLoading) {
    return (
      <DashboardShell>
        <div className="space-y-6 animate-pulse">
          <div className="h-5 bg-muted rounded w-1/4" />
          <div className="h-28 bg-muted rounded-xl w-full" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2 space-y-4">
              <div className="h-6 bg-muted rounded w-1/3" />
              <div className="h-32 bg-muted rounded-xl w-full" />
              <div className="h-32 bg-muted rounded-xl w-full" />
            </div>
            <div className="h-48 bg-muted rounded-xl w-full" />
          </div>
        </div>
      </DashboardShell>
    );
  }

  // Fallback 404 state
  if (error || !lab) {
    return (
      <DashboardShell>
        <div className="rounded-xl border border-border bg-card p-12 text-center shadow-sm">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-500/10 border border-red-500/20">
            <AlertCircle className="h-6 w-6 text-red-500" />
          </div>
          <h3 className="mt-4 text-base font-bold text-foreground">Lab Not Found</h3>
          <p className="mt-1 text-xs text-muted-foreground max-w-sm mx-auto leading-relaxed">
            The lab resource you are requesting does not exist or has been removed from our index.
          </p>
          <Link href="/labs" className="inline-block mt-6">
            <Button className="bg-primary hover:bg-primary/95 text-primary-foreground rounded-md flex items-center space-x-2">
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Explorer</span>
            </Button>
          </Link>
        </div>
      </DashboardShell>
    );
  }

  const syllabus = generateDynamicSyllabus(lab.category, lab.title);

  return (
    <DashboardShell>
      {/* Breadcrumbs */}
      <div className="flex items-center space-x-1.5 text-xs text-muted-foreground">
        <Link href="/labs" className="hover:text-foreground transition-colors">
          Explorer
        </Link>
        <ChevronRight className="h-3 w-3" />
        <span className="text-foreground font-semibold truncate max-w-[200px]">{lab.title}</span>
      </div>

      {/* Hero Banner Header */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm relative overflow-hidden">
        <div className="relative z-10 space-y-4">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="inline-flex items-center space-x-1 font-bold text-primary bg-primary/10 border border-primary/20 px-2.5 py-0.5 rounded-full uppercase text-[9px]">
              {getCategoryIcon(lab.category)}
              <span>{lab.category}</span>
            </span>
            <span className="inline-flex items-center space-x-1 text-muted-foreground bg-muted border border-border/50 px-2.5 py-0.5 rounded-full uppercase text-[9px] font-semibold">
              <Clock className="h-3 w-3" />
              <span>{lab.duration}</span>
            </span>
            <span className="inline-flex items-center space-x-1 text-muted-foreground bg-muted border border-border/50 px-2.5 py-0.5 rounded-full uppercase text-[9px] font-semibold">
              <Sliders className="h-3 w-3" />
              <span>{lab.difficulty}</span>
            </span>
          </div>

          <h1 className="text-xl sm:text-2xl font-black text-foreground tracking-tight leading-tight">
            {lab.title}
          </h1>

          <p className="text-xs sm:text-sm text-muted-foreground max-w-2xl leading-relaxed">
            {lab.description}
          </p>
        </div>

        {/* Diagonal Background Accent */}
        <div className="absolute right-0 bottom-0 top-0 w-1/3 bg-gradient-to-l from-primary/5 to-transparent skew-x-12 transform pointer-events-none" />
      </div>

      {/* Dynamic Content Columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left main syllabus column */}
        <div className="md:col-span-2 space-y-6">
          {/* Objectives Card */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <h2 className="text-sm font-bold tracking-wider text-muted-foreground uppercase mb-4 flex items-center">
              <CheckCircle2 className="h-4 w-4 mr-2 text-primary" />
              <span>Learning Objectives</span>
            </h2>
            <ul className="space-y-3">
              {syllabus.objectives.map((obj, i) => (
                <li key={i} className="flex items-start text-xs text-foreground leading-relaxed">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary mt-1.5 mr-2.5 shrink-0" />
                  <span>{obj}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Topics Covered Card */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <h2 className="text-sm font-bold tracking-wider text-muted-foreground uppercase mb-4 flex items-center">
              <BookOpen className="h-4 w-4 mr-2 text-primary" />
              <span>Topics Covered</span>
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {syllabus.topics.map((topic, i) => (
                <div
                  key={i}
                  className="p-3 bg-muted/30 border border-border/40 rounded-lg text-xs font-semibold text-foreground flex items-center"
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-primary mr-2.5 shrink-0" />
                  <span>{topic}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right launcher sidebar column */}
        <div className="space-y-6">
          {/* Lab Config Launcher */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm flex flex-col justify-between h-full space-y-6">
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-foreground">Launch Environment</h3>
              
              {/* Alert status */}
              {lab.slug === "linux-command-line-basics" ? (
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-[11px] text-emerald-600 leading-relaxed flex items-start">
                  <CheckCircle2 className="h-4 w-4 mr-2 shrink-0 text-emerald-600" />
                  <span>
                    <strong>Lab Status: Active.</strong> The Ubuntu 24.04 command sandbox is live! Click Launch below to start the interactive lesson.
                  </span>
                </div>
              ) : (
                <div className="p-3 bg-primary/10 border border-primary/20 rounded-lg text-[11px] text-primary leading-relaxed flex items-start">
                  <AlertCircle className="h-4 w-4 mr-2 shrink-0 text-primary" />
                  <span>
                    <strong>Coming Soon:</strong> Interactive shell sandbox connections for this module will boot up in future releases.
                  </span>
                </div>
              )}

              {/* Prerequisites list */}
              <div className="space-y-2">
                <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                  Prerequisites
                </h4>
                <ul className="space-y-1.5">
                  {syllabus.prerequisites.map((prereq, i) => (
                    <li key={i} className="text-[11px] text-muted-foreground leading-relaxed flex items-start">
                      <span className="text-primary mr-1.5 select-none font-bold">•</span>
                      <span>{prereq}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Launch Action */}
            <div className="space-y-3 pt-4 border-t border-border/40">
              {lab.slug === "linux-command-line-basics" ? (
                <Link href="/labs/linux-basics" className="block w-full">
                  <Button
                    className="w-full bg-primary hover:bg-primary/95 text-primary-foreground py-2.5 rounded-md font-semibold text-xs shadow-sm border border-transparent"
                  >
                    Launch Lab
                  </Button>
                </Link>
              ) : (
                <Button
                  disabled
                  className="w-full bg-primary/40 text-primary-foreground/75 cursor-not-allowed py-2.5 rounded-md font-semibold text-xs shadow-sm border border-transparent"
                >
                  Coming Soon
                </Button>
              )}
              <Link href="/labs" className="block text-center text-xs text-muted-foreground hover:text-foreground">
                Back to Explorer
              </Link>
            </div>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
