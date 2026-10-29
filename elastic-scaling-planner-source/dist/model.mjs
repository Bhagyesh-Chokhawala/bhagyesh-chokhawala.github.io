export function calculate(p) {
  for (const [k,v] of Object.entries(p)) if(typeof v !== 'number'||!Number.isFinite(v)||v<0) throw Error('All parameters must be finite, nonnegative numbers.');
  for(const k of ['replicas','minimum','maximum','active','sessions','unresolved','regions','azs','regionLoss','azLoss']) if(!Number.isInteger(p[k])) throw Error('Replica, work, and failure-domain counts must be whole numbers.');
  if(p.tested<=0||p.util<=0||p.util>100) throw Error('Tested throughput must be positive and operating factor must be between 0 and 100%.');
  if(p.readyPercent>100) throw Error('Readiness contribution cannot exceed 100%.');
  if(p.regions<1||p.azs<1||p.regionLoss>p.regions||p.azLoss>p.azs) throw Error('Check Region/AZ counts and losses. Losses cannot exceed the configured counts.');
  const safe=p.tested*p.util/100;
  const capacity=p.replicas*safe*p.readyPercent/100;
  const horizon=p.delay+p.margin;
  const predicted=p.demand+p.growth*horizon;
  const raw=Math.ceil(predicted/safe);
  const target=Math.min(p.maximum,Math.max(p.minimum,raw));
  const conflict=p.minimum>p.maximum;
  const saturation=p.demand>=capacity?0:(p.growth>0?(capacity-p.demand)/p.growth:Infinity);
  const mu=Math.min(capacity,p.dependency);
  const integrate=(c,T)=>{const e=p.demand-c; if(!p.growth)return Math.max(0,e)*T;const a=Math.max(0,-e/p.growth);return a>=T?0:e*(T-a)+p.growth*(T*T-a*a)/2;};
  const deficit=integrate(mu,p.delay);
  const queueBudget=Math.max(0,Math.min(p.queue,mu*p.wait)-p.queued);
  const defer=Math.min(deficit,queueBudget);
  const spare=capacity-p.demand;
  const after=Math.min((p.replicas*p.readyPercent/100+Math.max(0,target-p.replicas))*safe,p.dependency);
  const drainClear=p.active===0&&p.sessions===0&&p.unresolved===0;
  const survivor=(p.regions-p.regionLoss)*(p.azs-p.azLoss)*p.azCapacity;
  const urgency=saturation<=horizon;
  const scaleOut=Math.max(0,target-p.replicas);
  return {safe,capacity,horizon,predicted,raw,target,conflict,saturation,mu,deficit,queueBudget,defer,
    rejected:Math.max(0,deficit-defer),spare,after,drainClear,survivor,urgency,scaleOut,
    ratio:horizon>0?saturation/horizon:null,replicaShortfall:Math.max(0,raw-target),
    latencyBudget:p.edge+p.app+p.db+p.response+p.latencyMargin,
    concurrency:p.demand*p.latency/1000};
}
