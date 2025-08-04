import {
  CopilotRuntime,
  copilotRuntimeNextJSAppRouterEndpoint,
  GoogleGenerativeAIAdapter
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";
 
// You can use any service adapter here for multi-agent support.
const serviceAdapter = new GoogleGenerativeAIAdapter();
 
const runtime = new CopilotRuntime();
 
export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });
 
  return handleRequest(req);
};