"use client"

import "@copilotkit/react-ui/styles.css";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function GoogleDeepMindChatUI() {
  const router = useRouter();

  useEffect(() => {
    router.push("/post-generator");
  }, [router]);

  return (
    <></>
  )
}
