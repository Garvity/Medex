import { useEffect, useRef, useState, RefObject } from 'react';

export function useScrollReveal(): [RefObject<HTMLDivElement>, boolean] {
  const ref = useRef<HTMLDivElement>(null) as RefObject<HTMLDivElement>;
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); obs.disconnect(); } },
      { threshold: 0.15 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return [ref, visible];
}
