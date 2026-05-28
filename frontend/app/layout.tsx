import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ResumeRadar — AI Job Match Engine",
  description:
    "Paste a job description and your resume. AI tells you fit score, missing skills, and rewrites your resume + cover letter to maximize match.",
  keywords: ["resume", "AI", "job match", "ATS", "cover letter", "skill gap"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className="antialiased">{children}</body>
    </html>
  );
}
