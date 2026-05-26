"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";
import { Loader2, LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { createSupabaseBrowserClient, isSupabaseConfigured } from "@/lib/supabase/client";

function LoginForm() {
  const searchParams = useSearchParams();
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!isSupabaseConfigured()) {
      setError("Supabase is not configured for this environment.");
      return;
    }

    const formData = new FormData(event.currentTarget);
    const email = String(formData.get("email") ?? "");
    const password = String(formData.get("password") ?? "");

    setIsSubmitting(true);
    try {
      const supabase = createSupabaseBrowserClient();
      const { error: loginError } = await supabase.auth.signInWithPassword({ email, password });
      if (loginError) {
        setError(loginError.message);
        return;
      }
      window.location.href = searchParams.get("next") ?? "/app";
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      <label className="block space-y-2 text-sm font-medium">
        <span>Email</span>
        <input className="w-full rounded-md border border-border px-3 py-2" name="email" type="email" required />
      </label>
      <label className="block space-y-2 text-sm font-medium">
        <span>Password</span>
        <input className="w-full rounded-md border border-border px-3 py-2" name="password" type="password" required />
      </label>
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      <Button className="w-full gap-2" disabled={isSubmitting} type="submit">
        {isSubmitting ? <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" /> : null}
        Log in
      </Button>
    </form>
  );
}

export default function LoginPage() {
  return (
    <main className="min-h-screen bg-background px-6 py-10">
      <section className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-md flex-col justify-center gap-8">
        <div className="space-y-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <LogIn aria-hidden="true" className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-3xl font-semibold tracking-normal">Log in</h1>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Continue to your protected Throughball workspace.
            </p>
          </div>
        </div>
        <Suspense>
          <LoginForm />
        </Suspense>
        <p className="text-sm text-muted-foreground">
          New to Throughball?{" "}
          <Link className="font-medium text-foreground underline underline-offset-4" href="/signup">
            Create account
          </Link>
        </p>
      </section>
    </main>
  );
}
