"use client"

import {
  ChevronDown,
  ChevronRight,
  Download,
  FileCode,
  FileImage,
  FileJson,
  FileSpreadsheet,
  Users,
} from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { MessageContentRenderer } from "./agent-message-renderers/message-content-renderer"
import { ChatMessageI } from "./message.interface"
import { AgentI } from "./agent-declaration"

// File type icons for attachments
const getFileIcon = (type: string) => {
  switch (type) {
    case "json":
      return <FileJson className="h-4 w-4" />
    case "csv":
      return <FileSpreadsheet className="h-4 w-4" />
    case "image":
      return <FileImage className="h-4 w-4" />
    default:
      return <FileCode className="h-4 w-4" />
  }
}

interface MessageProps {
    message: ChatMessageI
    agents: AgentI[]
}

// Message component for chat interface
export function Message({ message, agents }: MessageProps) {
  const [showAttachments, setShowAttachments] = useState(false)

  // Find agent details if this is an agent message
  const agent = message.agentId ? agents.find((a: any) => a.id === message.agentId) : null

  // Format timestamp
  const formattedTime = message.timestamp || new Date().toLocaleTimeString()

  return (
    <div
      className={`flex gap-3 mb-4 ${
        message.role === "user" ? "flex-row-reverse" : message.role === "system" ? "justify-center" : ""
      }`}
    >
      {message.role === "agent" && agent && (
        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${agent.color}`}>{agent.icon}</div>
      )}

      {message.role === "user" && (
        <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center">
          <Users className="h-4 w-4" />
        </div>
      )}

      <div
        className={`max-w-[80%] rounded-lg p-3 ${
          message.role === "user"
            ? "bg-blue-600 text-white"
            : message.role === "system"
              ? "bg-slate-700 text-slate-300 text-xs px-3 py-1 mx-auto"
              : message.role === "agent" && agent
                ? `bg-slate-800 border ${agent.borderColor}`
                : "bg-slate-800 border border-slate-700"
        }`}
      >
        {message.role === "agent" && agent && (
          <div className={`text-xs font-medium mb-1 ${agent.textColor}`}>{agent.name}</div>
        )}

        {/* Use the MessageContentRenderer for the message content */}
        <MessageContentRenderer message={message} agents={agents} />

        {/* {message.attachments && message.attachments.length > 0 && (
          <div className="mt-2">
            <button
              onClick={() => setShowAttachments(!showAttachments)}
              className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-300"
            >
              {showAttachments ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              {message.attachments.length} attachment{message.attachments.length !== 1 ? "s" : ""}
            </button>

            {showAttachments && (
              <div className="mt-2 space-y-2">
                {message.attachments.map((attachment: any, index: any) => (
                  <div
                    key={index}
                    className="flex items-center gap-2 p-2 rounded bg-slate-900 text-xs border border-slate-700"
                  >
                    {getFileIcon(attachment.type)}
                    <div className="flex-1">
                      <div className="font-medium">{attachment.name}</div>
                      <div className="text-slate-400 text-xs truncate">{attachment.preview}</div>
                    </div>
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                      <Download className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )} */}

        <div className="text-xs text-slate-400 mt-1 text-right">{formattedTime}</div>
      </div>
    </div>
  )
}
