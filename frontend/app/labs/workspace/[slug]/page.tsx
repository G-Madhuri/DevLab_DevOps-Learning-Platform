"use client";

import React from "react";
import { useParams } from "next/navigation";
import { CourseViewer } from "@/components/ui/course-viewer";

export default function WorkspaceLabPage() {
  const params = useParams();
  const slug = params.slug as string;
  
  // Format slug to readable title (e.g. linux-command-line-basics -> Linux Command Line Basics)
  const title = slug
    .split("-")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");

  return (
    <CourseViewer
      courseSlug={slug}
      courseTitle={title}
    />
  );
}
