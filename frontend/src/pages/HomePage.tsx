import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { MessageSquare, Brain, Shield, Zap, ArrowRight, Sparkles } from 'lucide-react';
import { useScrollReveal } from '../hooks/useScrollReveal';

const features = [
  { icon: Brain, title: 'Hybrid RAG', desc: 'Multi-source retrieval across drugs, diseases, and nutrition databases' },
  { icon: Shield, title: 'Safety Fallback', desc: 'Built-in guardrails with emergency detection and clinical disclaimers' },
  { icon: Zap, title: 'Multi-Agent', desc: 'Intelligent tool routing for drug interactions, risk prediction, and reminders' },
  { icon: MessageSquare, title: 'Context Memory', desc: 'Conversation-aware retrieval for seamless follow-up questions' },
];

const stats = [
  { value: '10K+', label: 'Medical Entries' },
  { value: '99.2%', label: 'Uptime' },
  { value: '<1s', label: 'Response Time' },
  { value: '5+', label: 'AI Agents' },
];

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.12 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30, scale: 0.95 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } },
};

function ScrollRevealSection({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  const [ref, visible] = useScrollReveal();
  return (
    <div ref={ref} className={className}>
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={visible ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      >
        {children}
      </motion.div>
    </div>
  );
}

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <motion.main
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="flex-1 overflow-y-auto relative z-10"
    >
      <div className="max-w-5xl mx-auto px-6 py-16 md:py-24">
        {/* ── HERO ── */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="text-center mb-24"
        >
          {/* Floating icon with rings */}
          <motion.div variants={itemVariants} className="relative w-24 h-24 mx-auto mb-10">
            <motion.div
              animate={{ scale: [1, 1.15, 1], opacity: [0.3, 0.6, 0.3] }}
              transition={{ duration: 3, repeat: Infinity }}
              className="absolute inset-0 rounded-3xl border-2 border-primary/20"
            />
            <motion.div
              animate={{ scale: [1, 1.25, 1], opacity: [0.15, 0.35, 0.15] }}
              transition={{ duration: 3, repeat: Infinity, delay: 0.5 }}
              className="absolute -inset-3 rounded-3xl border border-primary/10"
            />
            <motion.div
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
              className="relative w-24 h-24 rounded-3xl bg-gradient-to-br from-primary to-secondary p-1 shadow-2xl shadow-primary/25"
            >
              <img src="/medical-logo.png" alt="MedAssist logo" className="w-full h-full rounded-[20px] object-cover" />
            </motion.div>
          </motion.div>

          <motion.div variants={itemVariants} className="flex items-center justify-center gap-2 mb-6">
            <Sparkles size={14} className="text-primary" />
            <span className="text-xs font-semibold uppercase tracking-[3px] text-primary">AI-Powered Healthcare</span>
            <Sparkles size={14} className="text-primary" />
          </motion.div>

          <motion.h1 variants={itemVariants} className="text-5xl md:text-7xl lg:text-8xl font-extrabold tracking-tighter mb-6 leading-[0.9]">
            <span className="text-gradient">Medical AI</span>
            <br />
            <span className="text-foreground">Assistant</span>
          </motion.h1>

          <motion.p variants={itemVariants} className="text-muted-foreground text-lg md:text-xl max-w-2xl mx-auto mb-12 leading-relaxed">
            Intelligent healthcare assistant powered by hybrid retrieval, multi-agent reasoning, and clinical health tools.
          </motion.p>

          <motion.div variants={itemVariants}>
            <motion.button
              whileHover={{ scale: 1.04, boxShadow: '0 0 50px hsl(162 72% 42% / 0.35)' }}
              whileTap={{ scale: 0.97 }}
              onClick={() => navigate('/chat')}
              className="group inline-flex items-center gap-3 px-9 py-4.5 rounded-2xl bg-gradient-to-r from-primary to-secondary text-primary-foreground font-semibold text-base shadow-xl shadow-primary/25 transition-all"
            >
              Start Consultation
              <motion.span animate={{ x: [0, 4, 0] }} transition={{ duration: 1.5, repeat: Infinity }}>
                <ArrowRight size={18} />
              </motion.span>
            </motion.button>
          </motion.div>
        </motion.div>

        {/* ── STATS ── */}
        <ScrollRevealSection className="mb-20">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {stats.map((s, i) => (
              <motion.div
                key={s.label}
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="glass rounded-2xl p-5 text-center group hover:glow-primary transition-shadow duration-300"
              >
                <div className="text-2xl md:text-3xl font-extrabold text-gradient mb-1">{s.value}</div>
                <div className="text-xs text-muted-foreground font-medium uppercase tracking-wider">{s.label}</div>
              </motion.div>
            ))}
          </div>
        </ScrollRevealSection>

        {/* ── FEATURES ── */}
        <ScrollRevealSection>
          <h2 className="text-center text-2xl font-bold text-foreground mb-10">
            Powered by <span className="text-gradient">Advanced AI</span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                whileHover={{ y: -6, transition: { duration: 0.25 } }}
                className="glass rounded-2xl p-6 group cursor-default"
              >
                <motion.div
                  whileHover={{ rotate: [0, -8, 8, 0], scale: 1.1 }}
                  transition={{ duration: 0.4 }}
                  className="w-12 h-12 rounded-xl bg-primary/15 flex items-center justify-center mb-4 group-hover:glow-primary transition-shadow duration-300"
                >
                  <f.icon size={22} className="text-primary" />
                </motion.div>
                <h3 className="text-foreground font-semibold text-base mb-2">{f.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </ScrollRevealSection>
      </div>
    </motion.main>
  );
}
