// src/components/epreuve/DistributionChart.jsx
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';

export default function DistributionChart({ data, seuil }) {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg border border-dashed border-gray-200">
        <span className="text-gray-400">Aucune donnée disponible</span>
      </div>
    );
  }

  const seuilValue = parseFloat(seuil);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-100 shadow-lg rounded-lg">
          <p className="text-sm font-semibold text-gray-700 mb-1">Notes: {label}</p>
          <p className="text-sm text-blue-600 font-medium">
            {payload[0].value} candidat{payload[0].value > 1 ? 's' : ''}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <XAxis dataKey="tranche" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6B7280' }} />
          <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6B7280' }} allowDecimals={false} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: '#F3F4F6' }} />
          <ReferenceLine x={data.find(d => seuilValue >= d.borne_inf && seuilValue < d.borne_sup)?.tranche || data[data.length - 1].tranche} stroke="#EF4444" strokeDasharray="3 3" label={{ position: 'top', value: 'Seuil', fill: '#EF4444', fontSize: 12, fontWeight: 'bold' }} />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.borne_inf >= seuilValue ? '#10B981' : '#F87171'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
