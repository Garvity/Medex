import { motion } from 'framer-motion';
import { User, Bot } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Message {
  user: string;
  bot: string;
  role: string;
  createdAt: string;
}

export default function ChatMessage({ message }: { message: Message }) {
  const ts = message.createdAt
    ? new Date(message.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';

  return (
    <div className="flex flex-col gap-4">
      {/* User Message */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-end gap-3"
      >
        <div className="max-w-[80%] rounded-2xl rounded-tr-none px-5 py-3.5 bg-primary/10 border border-primary/30 text-foreground shadow-lg hover:border-primary/40 transition-all duration-200">
          <span className="text-[9px] font-bold uppercase tracking-wider text-primary/70 block mb-1.5">
            {message.role === 'doctor' ? '🩺 Clinician' : '👤 You'}
          </span>
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.user}</p>
          {ts && <span className="text-[9px] text-muted-foreground block mt-2 text-right">{ts}</span>}
        </div>
        <div className="w-8 h-8 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center flex-shrink-0 mt-1 shadow-inner">
          <User size={13} className="text-primary" />
        </div>
      </motion.div>

      {/* Bot Message */}
      {message.bot && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="flex justify-start gap-3"
        >
          <div className="w-8 h-8 rounded-xl bg-card border border-border flex items-center justify-center flex-shrink-0 mt-1 shadow-md relative glow-neon">
            <Bot size={13} className="text-primary animate-pulse" />
          </div>
          <div className="max-w-[80%] rounded-2xl rounded-tl-none px-5 py-3.5 glass border border-border/80 text-card-foreground shadow-lg hover:border-primary/20 transition-all duration-200">
            <span className="text-[9px] font-bold uppercase tracking-wider text-primary/70 block mb-1.5">
              MedAssist AI
            </span>
            <div className="text-sm leading-relaxed text-foreground/90 markdown-content">
              <ReactMarkdown>{message.bot}</ReactMarkdown>
            </div>
            {ts && <span className="text-[9px] text-muted-foreground block mt-2">{ts}</span>}
          </div>
        </motion.div>
      )}
    </div>
  );
}
