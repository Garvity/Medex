import { motion } from 'framer-motion';
import { Database, Cpu, Shield, Layers, GitBranch, Zap } from 'lucide-react';
import { useScrollReveal } from '../hooks/useScrollReveal';

const stack = [
  { icon: Database, title: 'Hybrid RAG', desc: 'Dense + sparse retrieval across medical, drug, disease, and nutrition knowledge bases' },
  { icon: Cpu, title: 'Multi-Agent Pipeline', desc: 'Tool agent routes queries to specialized tools: drug interactions, risk prediction, reminders' },
  { icon: Shield, title: 'Safety Layer', desc: 'Emergency detection, clinical disclaimers, and fallback handling for out-of-scope queries' },
  { icon: Layers, title: 'Vector Store', desc: 'ChromaDB-powered vector database with medical embeddings for semantic search' },
  { icon: GitBranch, title: 'Conversation Memory', desc: 'Context-aware retrieval using conversation history for follow-up questions' },
  { icon: Zap, title: 'FastAPI Backend', desc: 'High-performance REST API with health checks, prediction, and interaction endpoints' },
];

function RevealCard({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const [ref, visible] = useScrollReveal();
  return (
    <div ref={ref}>
      <motion.div
        initial={{ opacity: 0, y: 40, scale: 0.95 }}
        animate={visible ? { opacity: 1, y: 0, scale: 1 } : {}}
        transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
      >
        {children}
      </motion.div>
    </div>
  );
}

export default function AboutPage() {
  return (
    <motion.main
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="flex-1 overflow-y-auto relative z-10"
    >
      <div className="max-w-4xl mx-auto px-6 py-16">
        <motion.div
          initial={{ y: 30, opacity: 0, scale: 0.97 }}
          animate={{ y: 0, opacity: 1, scale: 1 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="mb-16 text-center"
        >
          <motion.div
            animate={{ y: [0, -6, 0] }}
            transition={{ duration: 4, repeat: Infinity }}
            className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-primary to-secondary p-1 shadow-xl shadow-primary/20"
          >
            <img src="/medical-logo.png" alt="MedAssist logo" className="w-full h-full rounded-xl object-cover" />
          </motion.div>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-4">
            <span className="text-gradient">About</span>{' '}
            <span className="text-foreground">MedAssist AI</span>
          </h1>
          <p className="text-muted-foreground text-base max-w-2xl mx-auto leading-relaxed">
            An AI-powered medical assistant built with hybrid retrieval-augmented generation,
            multi-agent orchestration, and clinical health tools for intelligent healthcare insights.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {stack.map((s, i) => (
            <RevealCard key={s.title} delay={i * 0.08}>
              <motion.div
                whileHover={{ y: -5, transition: { duration: 0.2 } }}
                className="glass rounded-2xl p-6 group h-full"
              >
                <motion.div
                  whileHover={{ rotate: [0, -10, 10, 0], scale: 1.1 }}
                  transition={{ duration: 0.4 }}
                  className="w-11 h-11 rounded-xl bg-primary/15 flex items-center justify-center mb-4 group-hover:glow-primary transition-shadow duration-300"
                >
                  <s.icon size={20} className="text-primary" />
                </motion.div>
                <h3 className="text-foreground font-semibold mb-2">{s.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{s.desc}</p>
              </motion.div>
            </RevealCard>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 }}
          className="mt-16 text-center"
        >
          <p className="text-muted-foreground text-xs">
            ⚠️ This is an AI assistant for informational purposes only. Always consult a qualified healthcare professional for medical advice.
          </p>
        </motion.div>
      </div>
    </motion.main>
  );
}
