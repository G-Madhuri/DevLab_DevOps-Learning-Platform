"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import {
  Terminal,
  Layers,
  Container,
  Cpu,
  Globe,
  Settings,
  ShieldCheck,
  Zap,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

export default function LandingPage() {
  const { isAuthenticated } = useAuth();
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const features = [
    {
      icon: <Terminal className="h-6 w-6 text-primary" />,
      title: "Learn Linux",
      description: "Master the command line, filesystem manipulation, shell scripting, and basic process management in real sandboxed systems.",
    },
    {
      icon: <Container className="h-6 w-6 text-primary" />,
      title: "Learn Docker",
      description: "Build efficient custom images, orchestrate multi-container microservices, manage networks, and scale runtimes.",
    },
    {
      icon: <Layers className="h-6 w-6 text-primary" />,
      title: "Learn Kubernetes",
      description: "Deploy production clusters, manage multi-node pods, configure ingress controllers, and scale replicas dynamically.",
    },
    {
      icon: <Cpu className="h-6 w-6 text-primary" />,
      title: "Learn Terraform",
      description: "Write clean declarative IaC configurations, perform planning dry-runs, and track state changes dynamically.",
    },
    {
      icon: <Globe className="h-6 w-6 text-primary" />,
      title: "Learn AWS & Azure",
      description: "Simulate cloud computing resources, set up object storage Buckets, configure IAM security policies, and manage cloud endpoints.",
    },
  ];

  const faqs = [
    {
      q: "How do isolated labs work?",
      a: "Each lab runs in a secure, containerized sandbox isolated from other users. When you click launch, we provision the resource instantly inside our cloud pool.",
    },
    {
      q: "Do labs expire?",
      a: "Yes, to manage cloud resources responsibly, each sandbox has a countdown timer (e.g. 60 minutes) and automatically tears down upon expiration.",
    },
    {
      q: "What technologies are available in Phase 1?",
      a: "Phase 1 focuses on establishing the SaaS framework (auth, dashboard, profile, and settings). Future phases will integrate direct terminal consoles for Linux, Docker, K8s, Terraform, and cloud labs.",
    },
    {
      q: "Can I track my progress?",
      a: "Yes, in future phases, we will introduce modules tracking your XP, completed lab credentials, and career certifications.",
    },
  ];

  const toggleFaq = (index: number) => {
    setOpenFaq(openFaq === index ? null : index);
  };

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />

      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 lg:py-32 bg-slate-50 dark:bg-slate-950/20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 gap-12 lg:grid-cols-2 items-center">
            {/* Headline and Copy */}
            <div className="space-y-6 text-left">
              <div className="inline-flex items-center space-x-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs text-primary font-medium">
                <Zap className="h-3 w-3 animate-pulse" />
                <span>Phase 1: SaaS Foundation is Live</span>
              </div>
              <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl text-foreground">
                Master DevOps with{" "}
                <span className="text-primary">Hands-on Cloud Labs</span>
              </h1>
              <p className="text-base sm:text-lg text-muted-foreground leading-relaxed max-w-xl">
                Provision isolated Linux, Docker, and Kubernetes sandboxes with one click. Run exercises directly in your browser with zero local setups.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                {isAuthenticated ? (
                  <Link href="/dashboard">
                    <Button size="lg" className="w-full sm:w-auto bg-primary hover:bg-primary/90 text-primary-foreground font-medium rounded-md px-8 py-3 shadow-md transition-all">
                      Go to Dashboard
                    </Button>
                  </Link>
                ) : (
                  <>
                    <Link href="/register">
                      <Button size="lg" className="w-full sm:w-auto bg-primary hover:bg-primary/90 text-primary-foreground font-medium rounded-md px-8 py-3 shadow-md transition-all">
                        Get Started
                      </Button>
                    </Link>
                    <Link href="/login">
                      <Button size="lg" variant="outline" className="w-full sm:w-auto font-medium rounded-md px-8 py-3">
                        Login
                      </Button>
                    </Link>
                  </>
                )}
              </div>
            </div>

            {/* Premium Terminal SVG Illustration */}
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-tr from-primary/10 to-indigo-500/10 rounded-xl blur-2xl" />
              <svg
                viewBox="0 0 600 400"
                className="relative w-full h-auto rounded-xl overflow-hidden border border-border shadow-lg bg-card"
              >
                {/* OS Header Bar */}
                <rect width="600" height="40" className="fill-slate-100 dark:fill-slate-900" />
                <circle cx="20" cy="20" r="6" fill="#ef4444" />
                <circle cx="40" cy="20" r="6" fill="#f59e0b" />
                <circle cx="60" cy="20" r="6" fill="#10b981" />
                <text
                  x="300"
                  y="25"
                  textAnchor="middle"
                  fontSize="12"
                  className="fill-slate-500 font-mono"
                >
                  root@devlab:~
                </text>

                {/* Shell Workspace */}
                <rect y="40" width="600" height="360" className="fill-slate-950" />
                <text x="25" y="80" fill="#10b981" fontFamily="monospace" fontSize="14">
                  $ devlab launch-lab --type=docker
                </text>
                <text x="25" y="110" fill="#64748b" fontFamily="monospace" fontSize="12">
                  Provisioning isolated container sandbox...
                </text>
                <text x="25" y="130" fill="#64748b" fontFamily="monospace" fontSize="12">
                  Allocating resources: 1 CPU, 2GB RAM
                </text>
                <text x="25" y="150" fill="#10b981" fontFamily="monospace" fontSize="12">
                  ✔ Docker lab launched successfully (active for 60m)
                </text>
                <text x="25" y="180" fill="#f8fafc" fontFamily="monospace" fontSize="14">
                  $ docker run -d -p 80:80 nginx
                </text>
                <text x="25" y="210" fill="#64748b" fontFamily="monospace" fontSize="12">
                  Unable to find image &apos;nginx:latest&apos; locally
                </text>
                <text x="25" y="230" fill="#64748b" fontFamily="monospace" fontSize="12">
                  latest: Pulling from library/nginx
                </text>
                <text x="25" y="250" fill="#10b981" fontFamily="monospace" fontSize="12">
                  ✔ Digest: sha256:0d17b5e52...
                </text>
                <text x="25" y="270" fill="#10b981" fontFamily="monospace" fontSize="12">
                  ✔ Status: Downloaded newer image for nginx:latest
                </text>
                <text x="25" y="290" fill="#f8fafc" fontFamily="monospace" fontSize="12">
                  3067980cdb90a6e8b2bcf39c2d12...
                </text>
                <text x="25" y="320" fill="#f8fafc" fontFamily="monospace" fontSize="14">
                  $ _
                </text>
              </svg>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid Section */}
      <section id="features" className="py-20 bg-background">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center space-y-12">
          <div className="space-y-4 max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Cloud Environments Ready In Seconds
            </h2>
            <p className="text-muted-foreground text-sm sm:text-base">
              Learn critical engineering paradigms by deploying systems directly into micro sandboxes.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feat, index) => (
              <div
                key={index}
                className="flex flex-col items-start text-left p-6 border border-border rounded-xl bg-card transition-all hover:shadow-sm"
              >
                <div className="mb-4 rounded-lg bg-primary/10 p-3">{feat.icon}</div>
                <h3 className="text-lg font-semibold mb-2">{feat.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  {feat.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why DevLab Section */}
      <section id="why-devlab" className="py-20 bg-slate-50 dark:bg-slate-950/20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center space-y-4 max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Why Learn on DevLab?
            </h2>
            <p className="text-muted-foreground text-sm sm:text-base">
              Traditional courses use video formats. DevLab utilizes interactive terminal systems.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-6 text-center space-y-3 bg-card border border-border rounded-xl">
              <Zap className="h-10 w-10 text-primary mx-auto" />
              <h3 className="font-semibold text-lg">Zero Installation</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Skip complicated setup instructions. Launch runtime systems directly inside your browser container.
              </p>
            </div>
            <div className="p-6 text-center space-y-3 bg-card border border-border rounded-xl">
              <ShieldCheck className="h-10 w-10 text-primary mx-auto" />
              <h3 className="font-semibold text-lg">Secure Isolation</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Play inside dedicated sandboxes. Break and fix servers freely without risking actual cloud expenses.
              </p>
            </div>
            <div className="p-6 text-center space-y-3 bg-card border border-border rounded-xl">
              <Settings className="h-10 w-10 text-primary mx-auto" />
              <h3 className="font-semibold text-lg">Automatic Cleanup</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Sandbox instances automatically terminate after your time expires, keeping our compute clean and lightweight.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section with Custom Accordion */}
      <section id="faq" className="py-20 bg-background">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 space-y-10">
          <div className="text-center space-y-4">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Frequently Asked Questions
            </h2>
            <p className="text-muted-foreground text-sm">
              Answers to standard questions regarding our learning platform.
            </p>
          </div>
          <div className="border border-border rounded-xl divide-y divide-border bg-card overflow-hidden">
            {faqs.map((faq, index) => {
              const isOpen = openFaq === index;
              return (
                <div key={index} className="transition-all duration-200">
                  <button
                    onClick={() => toggleFaq(index)}
                    className="flex w-full items-center justify-between px-6 py-4 text-left font-medium text-foreground hover:bg-muted/50 transition-colors"
                  >
                    <span>{faq.q}</span>
                    {isOpen ? (
                      <ChevronUp className="h-4 w-4 text-muted-foreground shrink-0 ml-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0 ml-4" />
                    )}
                  </button>
                  {isOpen && (
                    <div className="px-6 pb-4 pt-1 text-muted-foreground text-sm leading-relaxed border-t border-border/20 bg-muted/10">
                      {faq.a}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
