import {
  CopilotRuntime,
  copilotRuntimeNextJSAppRouterEndpoint,
  GoogleGenerativeAIAdapter,
  LangGraphAgent
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";
 
// You can use any service adapter here for multi-agent support.
const serviceAdapter = new GoogleGenerativeAIAdapter();
 
const runtime = new CopilotRuntime({
  remoteEndpoints : [{
    url : "http://localhost:8000/copilotkit",
  }]
  // agents : {
  //   post_generation_agent : new LangGraphAgent({
  //     deploymentUrl : "http://localhost:8000/copilotkit",
  //     graphId : "post_generation_agent"
  //   })
  // }
});
 
export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });
 
  return handleRequest(req);
};