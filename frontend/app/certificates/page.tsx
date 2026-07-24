"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { labService } from "@/services/lab.service";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Award, Calendar, Search, ShieldCheck, Download, ExternalLink, Printer } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function CertificatesPage() {
  const [filterType, setFilterType] = useState<"all" | "course" | "academy">("all");
  const [search, setSearch] = useState("");
  const [selectedCert, setSelectedCert] = useState<any | null>(null);

  const { data: certificates = [], isLoading } = useQuery({
    queryKey: ["certificates_list"],
    queryFn: () => labService.listCertificates(),
  });

  const filteredCerts = certificates.filter((cert: any) => {
    const matchesSearch =
      cert.title.toLowerCase().includes(search.toLowerCase()) ||
      cert.target_title.toLowerCase().includes(search.toLowerCase());
    const matchesType = filterType === "all" || cert.type === filterType;
    return matchesSearch && matchesType;
  });

  const printCert = () => {
    window.print();
  };

  return (
    <DashboardShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <div>
            <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
              My Certifications
            </h1>
            <p className="text-sm text-muted-foreground">
              Verify, view, and share your earned DevOps credentials and academy certificates.
            </p>
          </div>
        </div>

        {/* Toolbar */}
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search certificates..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-md border border-border bg-card py-2 pl-10 pr-4 text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          <div className="flex bg-muted rounded-md p-1 border border-border/40">
            <button
              onClick={() => setFilterType("all")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors ${
                filterType === "all"
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterType("course")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors ${
                filterType === "course"
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Courses
            </button>
            <button
              onClick={() => setFilterType("academy")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors ${
                filterType === "academy"
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Academies
            </button>
          </div>
        </div>

        {/* Content Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-48 rounded-xl border border-border bg-card animate-pulse" />
            ))}
          </div>
        ) : filteredCerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border p-12 text-center bg-card">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Award className="h-6 w-6" />
            </div>
            <h3 className="mt-4 text-base font-bold text-foreground">No certifications earned yet</h3>
            <p className="mt-2 text-sm text-muted-foreground max-w-sm">
              Complete any course or full technology academy with 100% progress steps to unlock your official PDF credential.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCerts.map((cert: any) => (
              <div
                key={cert.id}
                onClick={() => setSelectedCert(cert)}
                className="group relative flex flex-col justify-between overflow-hidden rounded-xl border border-border bg-card p-5 hover:border-primary/50 hover:shadow-md cursor-pointer transition-all duration-300"
              >
                {/* Premium Card Border Highlight */}
                <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${
                  cert.type === "academy" 
                    ? "from-amber-500 to-yellow-400" 
                    : "from-blue-600 to-indigo-500"
                }`} />

                <div className="space-y-3">
                  <div className="flex justify-between items-start">
                    <div className={`p-2 rounded-lg ${
                      cert.type === "academy" ? "bg-amber-500/10 text-amber-500" : "bg-primary/10 text-primary"
                    }`}>
                      <Award className="h-5 w-5" />
                    </div>
                    <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-muted border border-border text-muted-foreground">
                      {cert.type}
                    </span>
                  </div>

                  <div>
                    <h3 className="font-bold text-foreground group-hover:text-primary transition-colors text-sm line-clamp-1">
                      {cert.title}
                    </h3>
                    <p className="text-xs text-muted-foreground mt-1">
                      Recipient: <span className="font-semibold text-foreground">{cert.recipient_name}</span>
                    </p>
                  </div>
                </div>

                <div className="mt-6 pt-3 border-t border-border/40 flex items-center justify-between text-[11px] text-muted-foreground">
                  <span className="flex items-center space-x-1">
                    <Calendar className="h-3 w-3" />
                    <span>{new Date(cert.issue_date).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })}</span>
                  </span>
                  <span className="font-mono text-primary font-bold group-hover:underline flex items-center space-x-1">
                    <span>View Certificate</span>
                    <ExternalLink className="h-3 w-3" />
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* High Fidelity Certificate Viewer Modal */}
      {selectedCert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in">
          <div className="relative w-full max-w-4xl rounded-2xl border border-border bg-card p-6 shadow-2xl space-y-6">
            {/* Action buttons (won't display during printing) */}
            <div className="flex justify-between items-center border-b border-border pb-4 print:hidden">
              <h2 className="text-lg font-bold text-foreground">Certificate View</h2>
              <div className="flex items-center space-x-2">
                <Button onClick={printCert} variant="outline" className="flex items-center space-x-1.5 text-xs">
                  <Printer className="h-4 w-4" />
                  <span>Print / Save PDF</span>
                </Button>
                <Button onClick={() => setSelectedCert(null)} variant="ghost" className="text-xs">
                  Close
                </Button>
              </div>
            </div>

            {/* Certificate Template Container */}
            <div 
              id="printable-certificate-template"
              className="relative aspect-[1.414/1] w-full border-[10px] border-double border-amber-800 bg-amber-50/20 rounded-lg p-8 md:p-12 flex flex-col justify-between items-center text-center shadow-inner overflow-hidden text-amber-900 animate-in zoom-in-95 duration-200"
            >
              {/* Premium Background Graphic */}
              <div className="absolute inset-0 opacity-[0.03] pointer-events-none select-none flex items-center justify-center">
                <Award className="w-[80%] h-[80%]" />
              </div>

              {/* Header */}
              <div className="space-y-2">
                <div className="flex items-center justify-center space-x-2 text-amber-700">
                  <ShieldCheck className="h-8 w-8" />
                  <span className="font-serif tracking-widest uppercase font-bold text-sm md:text-lg">DEVLAB SYSTEM CREDENTIAL</span>
                </div>
                <h4 className="text-[8px] md:text-xs tracking-widest text-amber-700/80 font-mono">CREDENTIAL VERIFICATION SECURE</h4>
              </div>

              {/* Declaration Statement */}
              <div className="space-y-4 md:space-y-6 my-auto">
                <p className="font-serif italic text-xs md:text-sm">This is proudly presented to</p>
                <h2 className="font-serif tracking-wide text-xl md:text-4xl font-extrabold uppercase border-b-2 border-amber-800/40 pb-2 px-8 min-w-[200px]">
                  {selectedCert.recipient_name}
                </h2>
                <p className="text-[10px] md:text-xs max-w-lg leading-relaxed font-sans px-4">
                  For outstanding academic excellence and successful completion of all laboratory validations, practical tasks, and grading thresholds for the course/academy:
                </p>
                <h3 className="font-serif text-sm md:text-2xl font-bold tracking-wide text-amber-800">
                  {selectedCert.target_title}
                </h3>
              </div>

              {/* Signatures & Footer details */}
              <div className="w-full flex justify-between items-end border-t border-amber-800/20 pt-4 md:pt-6 text-[8px] md:text-xs">
                <div className="space-y-0.5 md:space-y-1 text-left">
                  <p className="text-amber-800/70">VERIFICATION ID</p>
                  <p className="font-mono font-bold tracking-widest text-amber-900">{selectedCert.credential_id}</p>
                </div>

                <div className="flex flex-col items-center">
                  <Award className="h-8 w-8 md:h-10 md:w-10 text-amber-700" />
                  <p className="text-[6px] md:text-[8px] font-bold text-amber-700/80 mt-1">OFFICIAL SEAL</p>
                </div>

                <div className="space-y-0.5 md:space-y-1 text-right">
                  <p className="text-amber-800/70">ISSUE DATE</p>
                  <p className="font-bold">{new Date(selectedCert.issue_date).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
