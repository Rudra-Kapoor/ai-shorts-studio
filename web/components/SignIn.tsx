"use client";

import { useState } from "react";
import { signIn } from "@/lib/identity";

export default function SignIn({ onSignIn }: { onSignIn: () => void }) {
  const [email, setEmail] = useState("");
  return (
    <div className="card mx-auto mt-16 max-w-md p-8 text-center">
      <div className="mb-2 text-4xl">🎬</div>
      <h1 className="text-xl font-semibold">Welcome to AI Shorts Studio</h1>
      <p className="mt-2 text-sm text-gray-400">
        Enter an email to start. This is a demo identity stored on your device —
        no password needed.
      </p>
      <form
        className="mt-6 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (!email.includes("@")) return;
          signIn(email);
          onSignIn();
        }}
      >
        <input
          className="input"
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <button className="btn-primary whitespace-nowrap" type="submit">
          Continue
        </button>
      </form>
    </div>
  );
}
