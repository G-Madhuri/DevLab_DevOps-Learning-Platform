"use client";

import React, { useEffect, useRef, useState } from "react";
import { Loader2 } from "lucide-react";
import "xterm/css/xterm.css";

interface TerminalProps {
  sessionId: string;
  onClose?: () => void;
}

export function Terminal({ sessionId, onClose }: TerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const [connecting, setConnecting] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let term: any;
    let fitAddon: any;
    
    const initTerminal = async () => {
      if (!terminalRef.current) return;

      try {
        // Dynamically import xterm to bypass Next.js SSR document checks
        const { Terminal } = await import("xterm");
        const { FitAddon } = await import("xterm-addon-fit");

        // Construct WebSocket connection
        const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
        const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsHost = apiBase.replace(/^https?:\/\//, ""); // Remove protocol header
        const wsUrl = `${wsProtocol}//${wsHost}/labs/linux/session/${sessionId}/ws`;

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setConnecting(false);
          
          // Instantiate xterm
          term = new Terminal({
            cursorBlink: true,
            fontSize: 14,
            fontFamily: "Menlo, Monaco, 'Courier New', monospace",
            theme: {
              background: "#1C1824", // Matches dark surface colors
              foreground: "#EFEBF4", // Matches light text colors
              cursor: "#9B91F5",     // Soft purple accent cursor
            },
          });

          fitAddon = new FitAddon();
          term.loadAddon(fitAddon);
          term.open(terminalRef.current!);
          fitAddon.fit();

          // Handle console keys write to websocket
          term.onData((data: string) => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(data);
            }
          });

          // Resize handler
          window.addEventListener("resize", handleResize);
        };

        ws.onmessage = (event) => {
          if (term) {
            term.write(event.data);
          }
        };

        ws.onerror = (err) => {
          console.error("Terminal WebSocket error:", err);
          setError("Failed to establish server terminal connection.");
          setConnecting(false);
        };

        ws.onclose = () => {
          setConnecting(false);
          if (onClose) onClose();
        };

        const handleResize = () => {
          if (fitAddon) {
            fitAddon.fit();
          }
        };

      } catch (err: any) {
        console.error("Terminal initialization failed:", err);
        setError("Browser terminal failed to bootstrap.");
        setConnecting(false);
      }
    };

    initTerminal();

    // Cleanups on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (term) {
        term.dispose();
      }
      window.removeEventListener("resize", () => {});
    };
  }, [sessionId, onClose]);

  return (
    <div className="relative w-full h-[450px] bg-[#1C1824] rounded-xl border border-border p-3 overflow-hidden shadow-inner">
      {connecting && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#1C1824] text-[#EFEBF4] z-10 space-y-3">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <span className="text-xs text-[#AAA2B2]">Establishing secure SSH bridge...</span>
        </div>
      )}
      
      {error && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#1C1824] text-red-400 z-10 p-6 text-center space-y-2">
          <span className="text-sm font-bold">Connection Refused</span>
          <span className="text-xs text-[#AAA2B2] max-w-xs leading-normal">{error}</span>
        </div>
      )}

      {/* Terminal Viewport */}
      <div ref={terminalRef} className="w-full h-full" />
    </div>
  );
}
