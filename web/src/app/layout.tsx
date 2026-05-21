import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Chatoy",
  description: "Multi-agent direct-response marketing copilot",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
