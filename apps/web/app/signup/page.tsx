"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { Activity, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { createSupabaseBrowserClient, isSupabaseConfigured } from "@/lib/supabase/client";

export default function SignupPage() {
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");

    if (!isSupabaseConfigured()) {
      setError("Supabase is not configured for this environment.");
      return;
    }

    const formData = new FormData(event.currentTarget);
    const email = String(formData.get("email") ?? "");
    const password = String(formData.get("password") ?? "");
    const displayName = String(formData.get("display_name") ?? "");

    setIsSubmitting(true);
    try {
      const supabase = createSupabaseBrowserClient();
      const { data, error: signUpError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            display_name: displayName
          }
        }
      });

      if (signUpError) {
        setError(signUpError.message);
        return;
      }

      if (data.session) {
        window.location.href = "/onboarding";
      } else {
        setNotice("Check your email to confirm your account.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-background px-6 py-10">
      <section className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-md flex-col justify-center gap-8">
        <div className="space-y-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Activity aria-hidden="true" className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-3xl font-semibold tracking-normal">Create account</h1>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Use Supabase Auth directly with a minimal Throughball profile.
            </p>
          </div>
        </div>

        <form className="space-y-4" onSubmit={onSubmit}>
          <label className="block space-y-2 text-sm font-medium">
            <span>Email</span>
            <input className="w-full rounded-md border border-border px-3 py-2" name="email" type="email" required />
          </label>
          <label className="block space-y-2 text-sm font-medium">
            <span>Password</span>
            <input className="w-full rounded-md border border-border px-3 py-2" name="password" type="password" minLength={8} required />
          </label>
          <label className="block space-y-2 text-sm font-medium">
            <span>Display name</span>
            <input className="w-full rounded-md border border-border px-3 py-2" name="display_name" maxLength={50} />
          </label>
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
          {notice ? <p className="text-sm text-primary">{notice}</p> : null}
          <Button className="w-full gap-2" disabled={isSubmitting} type="submit">
            {isSubmitting ? <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" /> : null}
            Sign up
          </Button>
        </form>

        <p className="text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link className="font-medium text-foreground underline underline-offset-4" href="/login">
            Log in
          </Link>
        </p>
      </section>
    </main>
  );
}
