import { Activity, LogIn, UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <section className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center gap-8 px-6 py-16">
        <div className="space-y-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Activity aria-hidden="true" className="h-6 w-6" />
          </div>
          <h1 className="max-w-2xl text-4xl font-semibold tracking-normal text-foreground md:text-6xl">
            Throughball Platform
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-muted-foreground">
            Local-first foundation for the Next.js frontend and FastAPI operational backend.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button asChild className="gap-2">
            <a href="/signup">
              <UserPlus aria-hidden="true" className="h-4 w-4" />
              Sign up
            </a>
          </Button>
          <Button asChild className="gap-2" variant="secondary">
            <a href="/login">
              <LogIn aria-hidden="true" className="h-4 w-4" />
              Log in
            </a>
          </Button>
        </div>
      </section>
    </main>
  );
}
