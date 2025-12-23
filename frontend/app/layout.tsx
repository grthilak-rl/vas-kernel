import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

export const metadata: Metadata = {
  title: "VAS - Video Aggregation Service",
  description: "Professional video streaming and aggregation platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-gray-100">
        <div className="h-screen overflow-hidden flex flex-col">
          <Header />
          <div className="flex flex-1 overflow-hidden relative">
            <Sidebar />
            <main className="flex-1 md:ml-64 overflow-y-auto bg-gray-50 p-6">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}

