/**
 * frontend/src/lib/supabase.ts — Supabase JS Client Singleton
 *
 * Dùng cho Auth (sign_in, sign_up, sign_out, onAuthStateChange)
 * Sử dụng VITE_SUPABASE_URL và VITE_SUPABASE_ANON_KEY từ .env
 */
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = (import.meta.env.VITE_SUPABASE_URL as string) || "https://zwhoelltbonuzdophhhl.supabase.co";
const supabaseAnonKey = (import.meta.env.VITE_SUPABASE_ANON_KEY as string) || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp3aG9lbGx0Ym9udXpkb3BoaGhsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkwOTIzMDMsImV4cCI6MjEwNDY2ODMwM30.a_TRTqG3LH6vJz4qRDclspx3ueCYFD9h9ym_Rmy-ob8";

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
});

/** Kiểm tra email có đuôi @dlu.edu.vn */
export const isAllowedEmail = (email: string): boolean => {
  return email.toLowerCase().endsWith("@dlu.edu.vn");
};
