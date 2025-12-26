/**
 * AnalyticsCharts Component
 * 
 * Recharts-powered visualizations for form filling analytics.
 */

import {
    LineChart, Line,
    PieChart, Pie, Cell,
    BarChart, Bar,
    XAxis, YAxis,
    CartesianGrid, Tooltip,
    ResponsiveContainer, Legend
} from 'recharts';
import { useTheme } from '@/context/ThemeProvider';

// Chart color palette
const COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

export function SubmissionTrendChart({ data }) {
    const { isDark } = useTheme();

    return (
        <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#333' : '#e5e7eb'} />
                    <XAxis
                        dataKey="date"
                        stroke={isDark ? '#888' : '#6b7280'}
                        fontSize={12}
                    />
                    <YAxis
                        stroke={isDark ? '#888' : '#6b7280'}
                        fontSize={12}
                        allowDecimals={false}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: isDark ? '#1f2937' : '#fff',
                            border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                            borderRadius: '8px',
                            color: isDark ? '#fff' : '#000'
                        }}
                    />
                    <Line
                        type="monotone"
                        dataKey="count"
                        stroke="#10B981"
                        strokeWidth={3}
                        dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
                        activeDot={{ r: 6, fill: '#10B981' }}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}

export function SuccessRateChart({ successRate }) {
    const { isDark } = useTheme();

    const data = [
        { name: 'Success', value: successRate },
        { name: 'Failed', value: 100 - successRate },
    ];

    return (
        <div className="h-48 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={70}
                        paddingAngle={2}
                        dataKey="value"
                    >
                        <Cell fill="#10B981" />
                        <Cell fill={isDark ? '#374151' : '#e5e7eb'} />
                    </Pie>
                    <Tooltip
                        formatter={(value) => `${value}%`}
                        contentStyle={{
                            backgroundColor: isDark ? '#1f2937' : '#fff',
                            border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                            borderRadius: '8px',
                        }}
                    />
                </PieChart>
            </ResponsiveContainer>
            <div className="absolute text-center">
                <div className="text-2xl font-bold text-green-500">{successRate}%</div>
                <div className={`text-xs ${isDark ? 'text-white/50' : 'text-zinc-500'}`}>Success</div>
            </div>
        </div>
    );
}

export function FieldTypesChart({ data }) {
    const { isDark } = useTheme();

    return (
        <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data} layout="vertical" margin={{ top: 5, right: 20, left: 60, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#333' : '#e5e7eb'} />
                    <XAxis
                        type="number"
                        stroke={isDark ? '#888' : '#6b7280'}
                        fontSize={12}
                    />
                    <YAxis
                        type="category"
                        dataKey="name"
                        stroke={isDark ? '#888' : '#6b7280'}
                        fontSize={12}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: isDark ? '#1f2937' : '#fff',
                            border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                            borderRadius: '8px',
                        }}
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                        {data?.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}

export function FormTypeChart({ data }) {
    const { isDark } = useTheme();

    return (
        <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#333' : '#e5e7eb'} />
                    <XAxis
                        dataKey="type"
                        stroke={isDark ? '#888' : '#6b7280'}
                        fontSize={11}
                    />
                    <YAxis
                        stroke={isDark ? '#888' : '#6b7280'}
                        fontSize={12}
                        allowDecimals={false}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: isDark ? '#1f2937' : '#fff',
                            border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                            borderRadius: '8px',
                        }}
                    />
                    <Legend />
                    <Bar dataKey="success" stackId="a" fill="#10B981" name="Success" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="fail" stackId="a" fill="#EF4444" name="Failed" radius={[4, 4, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
