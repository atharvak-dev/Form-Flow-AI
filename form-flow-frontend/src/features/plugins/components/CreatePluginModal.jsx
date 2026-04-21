/**
 * Create Plugin Modal - Multi-step wizard
 * REDESIGNED: Premium SaaS Minimal Drawer (Vercel / Linear Style)
 */
import { useState, useCallback, useEffect, useRef, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
    X, ChevronLeft, ChevronRight, Database, Table2, Plus, Trash2,
    CheckCircle2, AlertCircle, Loader2, Server, Globe, ExternalLink
} from 'lucide-react';
import { useTheme } from '@/context/ThemeProvider';
import { PluginFormProvider, usePluginForm } from '../context/PluginFormContext';
import { useCreatePlugin } from '@/hooks/usePluginQueries';
import {
    pluginBasicInfoSchema,
    pluginConnectionSchema,
    columnTypes,
} from '../schemas/pluginSchemas';
import toast from 'react-hot-toast';

// ============ Reusable UI Components ============

const InputField = ({ label, error, required, ...props }) => {
    const { isDark } = useTheme();
    return (
        <div className="space-y-1.5">
            <label className={`text-[13px] font-medium ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
                {label} {required && <span className="text-emerald-500">*</span>}
            </label>
            <input
                {...props}
                className={`
                    w-full px-3.5 py-2.5 rounded-lg border text-[13px] font-medium transition-all shadow-sm
                    ${isDark
                        ? 'bg-zinc-900/50 border-white/[0.08] text-white placeholder:text-zinc-600 focus:border-emerald-500/50 focus:bg-zinc-900 focus:ring-4 focus:ring-emerald-500/10'
                        : 'bg-white border-zinc-200 text-zinc-900 placeholder:text-zinc-400 focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10'
                    }
                    focus:outline-none 
                `}
            />
            {error && <p className="text-xs font-medium text-red-500 mt-1">{error}</p>}
        </div>
    );
};

const CardSelector = ({ type, icon: Icon, isSelected, onClick, label, isDark }) => (
    <button
        type="button"
        onClick={onClick}
        className={`
            relative flex items-center gap-3 p-4 rounded-xl border transition-all duration-200 text-left
            ${isSelected
                ? isDark
                    ? 'bg-emerald-500/10 border-emerald-500/50 text-white'
                    : 'bg-emerald-50 border-emerald-500 text-emerald-900'
                : isDark
                    ? 'bg-zinc-900/40 border-white/[0.08] text-zinc-400 hover:border-white/[0.15] hover:bg-zinc-800/50'
                    : 'bg-white border-zinc-200 text-zinc-600 hover:border-zinc-300 hover:bg-zinc-50'
            }
        `}
    >
        <div className={`
            w-10 h-10 rounded-lg flex items-center justify-center shrink-0 transition-colors
            ${isSelected
                ? 'bg-emerald-500 text-white shadow-md shadow-emerald-500/20'
                : isDark ? 'bg-white/5 text-zinc-500' : 'bg-zinc-100 text-zinc-400'
            }
        `}>
            <Icon className="w-5 h-5" />
        </div>
        <div>
            <div className={`text-[13px] font-semibold ${isSelected ? (isDark ? 'text-white' : 'text-emerald-800') : (isDark ? 'text-zinc-300' : 'text-zinc-800')}`}>
                {label}
            </div>
            <div className={`text-[11px] mt-0.5 ${isSelected ? (isDark ? 'text-emerald-200' : 'text-emerald-600') : (isDark ? 'text-zinc-500' : 'text-zinc-500')}`}>
                Standard connection
            </div>
        </div>
        {isSelected && (
            <div className={`absolute top-3 right-3 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`}>
                <CheckCircle2 className="w-4 h-4" />
            </div>
        )}
    </button>
);

const CustomSelect = ({ value, onChange, options, isDark }) => {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (containerRef.current && !containerRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
        <div className="relative h-full w-full" ref={containerRef}>
            <button
                type="button"
                onClick={() => setIsOpen(!isOpen)}
                className={`
                    w-full h-full px-3.5 py-2.5 rounded-lg border text-[13px] font-medium transition-all shadow-sm flex items-center justify-between
                    ${isDark
                        ? 'bg-zinc-900/50 border-white/[0.08] text-white'
                        : 'bg-white border-zinc-200 text-zinc-900'
                    }
                    ${isOpen ? (isDark ? 'border-emerald-500/50 ring-4 ring-emerald-500/10' : 'border-emerald-500 ring-4 ring-emerald-500/10') : ''}
                `}
            >
                <span className={!value ? (isDark ? 'text-zinc-500' : 'text-zinc-400') : ''}>
                    {value || 'Select...'}
                </span>
                <ChevronLeft className={`w-3.5 h-3.5 transition-transform duration-200 ${isOpen ? 'rotate-90' : '-rotate-90'} ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`} />
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: -5, filter: 'blur(4px)' }}
                        animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                        exit={{ opacity: 0, y: -5, filter: 'blur(4px)' }}
                        transition={{ duration: 0.15 }}
                        className={`
                            absolute top-full mt-1.5 left-0 right-0 max-h-60 overflow-y-auto custom-scrollbar rounded-xl border shadow-xl z-[100]
                            ${isDark ? 'bg-zinc-900 border-white/[0.08]' : 'bg-white border-zinc-200'}
                        `}
                    >
                        <div className="p-1 space-y-0.5">
                            {options.map((option) => (
                                <button
                                    key={option}
                                    type="button"
                                    onClick={() => {
                                        onChange(option);
                                        setIsOpen(false);
                                    }}
                                    className={`
                                        w-full text-left px-3 py-2 rounded-md text-[13px] font-medium transition-colors flex items-center justify-between
                                        ${value === option
                                            ? (isDark ? 'bg-emerald-500/20 text-emerald-400' : 'bg-emerald-50 text-emerald-700')
                                            : (isDark ? 'text-zinc-300 hover:bg-white/[0.04]' : 'text-zinc-700 hover:bg-zinc-50')
                                        }
                                    `}
                                >
                                    {option}
                                    {value === option && <CheckCircle2 className="w-3.5 h-3.5" />}
                                </button>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

// ============ Step Components ============

function StepBasicInfo({ onNext }) {
    const { isDark } = useTheme();
    const { name, description, database_type, updateBasicInfo } = usePluginForm();

    const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm({
        resolver: zodResolver(pluginBasicInfoSchema),
        defaultValues: { name, description, database_type },
    });

    const currentType = watch('database_type');

    const onSubmit = (data) => {
        updateBasicInfo(data);
        onNext();
    };

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
            <div className="space-y-6">
                <InputField
                    label="Plugin Name"
                    required
                    placeholder="e.g. Lead Collection Form"
                    error={errors.name?.message}
                    {...register('name')}
                />

                <div className="space-y-1.5">
                    <label className={`text-[13px] font-medium ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
                        Description <span className="opacity-50 font-normal">(Optional)</span>
                    </label>
                    <textarea
                        {...register('description')}
                        placeholder="What is this plugin used for?"
                        rows={3}
                        className={`
                            w-full px-3.5 py-2.5 rounded-lg border text-[13px] font-medium transition-all shadow-sm
                            ${isDark
                                ? 'bg-zinc-900/50 border-white/[0.08] text-white placeholder:text-zinc-600 focus:border-emerald-500/50 focus:bg-zinc-900 focus:ring-4 focus:ring-emerald-500/10'
                                : 'bg-white border-zinc-200 text-zinc-900 placeholder:text-zinc-400 focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10'
                            }
                            focus:outline-none resize-none
                        `}
                    />
                </div>

                <div className="space-y-3">
                    <label className={`text-[13px] font-medium ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
                        Database Type <span className="text-emerald-500">*</span>
                    </label>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <CardSelector
                            type="postgresql"
                            icon={Database}
                            label="PostgreSQL"
                            isSelected={currentType === 'postgresql'}
                            onClick={() => setValue('database_type', 'postgresql')}
                            isDark={isDark}
                        />
                        <CardSelector
                            type="mysql"
                            icon={Server}
                            label="MySQL"
                            isSelected={currentType === 'mysql'}
                            onClick={() => setValue('database_type', 'mysql')}
                            isDark={isDark}
                        />
                    </div>
                    {errors.database_type && <p className="text-xs font-medium text-red-500 mt-1">{errors.database_type.message}</p>}
                </div>
            </div>

            <div className="pt-2">
                <button
                    type="submit"
                    className={`
                        w-full py-2.5 rounded-lg font-medium text-[13px] transition-colors shadow-sm
                        ${isDark
                            ? 'bg-white text-zinc-900 hover:bg-zinc-200'
                            : 'bg-zinc-900 text-white hover:bg-zinc-800'
                        }
                    `}
                >
                    Continue
                </button>
            </div>
        </form>
    );
}

function StepConnection({ onNext, onBack }) {
    const { isDark } = useTheme();
    const { connection_config, database_type, updateConnection } = usePluginForm();

    const { register, handleSubmit, formState: { errors } } = useForm({
        resolver: zodResolver(pluginConnectionSchema),
        defaultValues: connection_config,
    });

    const onSubmit = (data) => {
        updateConnection(data);
        onNext();
    };

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
            <div className="grid grid-cols-2 gap-x-4 gap-y-5">
                <div className="col-span-2 sm:col-span-1">
                    <InputField label="Host" required placeholder="db.example.com" error={errors.host?.message} {...register('host')} />
                </div>
                <div className="col-span-2 sm:col-span-1">
                    <InputField label="Port" required placeholder={database_type === 'postgresql' ? '5432' : '3306'} error={errors.port?.message} {...register('port', { valueAsNumber: true })} />
                </div>
                <div className="col-span-2">
                    <InputField label="Database / Schema" required placeholder="production_db" error={errors.database?.message} {...register('database')} />
                </div>
                <div className="col-span-2 sm:col-span-1">
                    <InputField label="Username" required placeholder="admin" error={errors.username?.message} {...register('username')} autoComplete="off" />
                </div>
                <div className="col-span-2 sm:col-span-1">
                    <InputField label="Password" required type="password" placeholder="••••••••" error={errors.password?.message} {...register('password')} autoComplete="new-password" />
                </div>
            </div>

            <div className={`p-4 rounded-xl border flex items-start gap-3 ${isDark ? 'bg-white/[0.02] border-white/[0.04]' : 'bg-zinc-50 border-zinc-200'}`}>
                <Globe className={`w-5 h-5 shrink-0 ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`} />
                <div className="flex-1">
                    <h5 className={`text-[13px] font-semibold ${isDark ? 'text-zinc-300' : 'text-zinc-800'}`}>Security Best Practices</h5>
                    <p className={`text-xs mt-1 leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>
                        Make sure to allowlist FormFlow's static IP addresses in your database firewall before proceeding. 
                        We recommend creating a restricted database user with only INSERT/SELECT privileges for this specific schema.
                    </p>
                </div>
            </div>

            <div className="flex gap-3 pt-2">
                <button
                    type="button"
                    onClick={onBack}
                    className={`
                        w-1/3 py-2.5 rounded-lg font-medium text-[13px] transition-colors
                        ${isDark ? 'bg-white/5 text-zinc-300 hover:bg-white/10' : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'}
                    `}
                >
                    Back
                </button>
                <button
                    type="submit"
                    className={`
                        w-2/3 py-2.5 rounded-lg font-medium text-[13px] transition-colors shadow-sm
                        ${isDark
                            ? 'bg-white text-zinc-900 hover:bg-zinc-200'
                            : 'bg-zinc-900 text-white hover:bg-zinc-800'
                        }
                    `}
                >
                    Continue
                </button>
            </div>
        </form>
    );
}

function StepTables({ onNext, onBack }) {
    const { isDark } = useTheme();
    const { tables, addTable, updateTable, removeTable, addField, updateField, removeField } = usePluginForm();

    const canProceed = tables.length > 0 && tables.every(
        (t) => t.table_name && t.fields.length > 0 && t.fields.every(
            (f) => f.column_name && f.column_type && f.question_text
        )
    );

    return (
        <div className="space-y-6">
            <div className="space-y-6">
                {tables.map((table, tableIdx) => (
                    <div
                        key={tableIdx}
                        className={`
                            rounded-2xl border overflow-hidden transition-all
                            ${isDark ? 'bg-zinc-900/40 border-white/[0.08]' : 'bg-white border-zinc-200 shadow-sm'}
                        `}
                    >
                        {/* Table Header */}
                        <div className={`flex items-center gap-4 px-5 py-4 border-b ${isDark ? 'bg-white/[0.02] border-white/[0.05]' : 'bg-zinc-50 border-zinc-100'}`}>
                            <div className={`p-1.5 rounded-md ${isDark ? 'bg-emerald-500/10' : 'bg-emerald-50'}`}>
                                <Table2 className={`w-4 h-4 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`} />
                            </div>
                            <input
                                type="text"
                                value={table.table_name}
                                onChange={(e) => updateTable(tableIdx, { table_name: e.target.value })}
                                placeholder="Schema Table Name..."
                                className={`
                                    flex-1 bg-transparent border-none text-[15px] font-semibold placeholder:font-normal focus:ring-0 p-0
                                    ${isDark ? 'text-zinc-100 placeholder:text-zinc-600' : 'text-zinc-900 placeholder:text-zinc-400'}
                                `}
                            />
                            <button
                                onClick={() => removeTable(tableIdx)}
                                className={`p-1.5 rounded-md transition-colors ${isDark ? 'hover:bg-white/[0.05] text-zinc-500 hover:text-red-400' : 'hover:bg-zinc-200 text-zinc-400 hover:text-red-500'}`}
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>

                        {/* Fields List */}
                        <div className="p-5 space-y-4">
                            {table.fields.map((field, fieldIdx) => (
                                <div key={fieldIdx} className={`grid grid-cols-12 gap-3 items-start pb-4 border-b last:border-0 last:pb-0 ${isDark ? 'border-white/[0.04]' : 'border-zinc-100'}`}>
                                    <div className="col-span-12 sm:col-span-3">
                                        <InputField label="Column Name" placeholder="e.g. first_name" value={field.column_name} onChange={(e) => updateField(tableIdx, fieldIdx, { column_name: e.target.value })} />
                                    </div>
                                    <div className="col-span-12 sm:col-span-3 h-[58px]">
                                        <label className={`block text-[13px] font-medium mb-1.5 ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
                                            Type
                                        </label>
                                        <CustomSelect
                                            value={field.column_type}
                                            onChange={(value) => updateField(tableIdx, fieldIdx, { column_type: value })}
                                            options={columnTypes}
                                            isDark={isDark}
                                        />
                                    </div>
                                    <div className="col-span-12 sm:col-span-5 relative">
                                        <InputField label="Agent Voice Prompt" placeholder="Ask the user..." value={field.question_text} onChange={(e) => updateField(tableIdx, fieldIdx, { question_text: e.target.value })} />
                                    </div>
                                    <div className="col-span-12 sm:col-span-1 flex justify-end sm:pt-7">
                                        <button
                                            onClick={() => removeField(tableIdx, fieldIdx)}
                                            disabled={table.fields.length === 1}
                                            className="p-1.5 hover:bg-red-500/10 text-zinc-400 hover:text-red-400 rounded-md transition-colors disabled:opacity-0"
                                        >
                                            <X className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            ))}

                            <button
                                onClick={() => addField(tableIdx)}
                                className={`
                                    flex items-center gap-2 text-[13px] font-semibold transition-colors mt-2
                                    ${isDark ? 'text-zinc-400 hover:text-white' : 'text-zinc-500 hover:text-zinc-900'}
                                `}
                            >
                                <Plus className="w-3.5 h-3.5" /> Add Attribute
                            </button>
                        </div>
                    </div>
                ))}

                <button
                    onClick={() => addTable()}
                    className={`
                        w-full py-4 rounded-xl border border-dashed flex items-center justify-center gap-2 text-[13px] font-medium transition-all
                        ${isDark
                            ? 'border-white/[0.08] text-zinc-400 hover:border-white/20 hover:text-white bg-white/[0.01]'
                            : 'border-zinc-200 text-zinc-600 hover:border-zinc-300 hover:text-zinc-900 bg-zinc-50/50'
                        }
                    `}
                >
                    <Plus className="w-4 h-4" /> Add Another Table
                </button>
            </div>

            <div className="flex gap-3 pt-6 border-t border-zinc-200 dark:border-white/[0.05]">
                <button
                    type="button"
                    onClick={onBack}
                    className={`
                        w-1/3 py-2.5 rounded-lg font-medium text-[13px] transition-colors
                        ${isDark ? 'bg-white/5 text-zinc-300 hover:bg-white/10' : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'}
                    `}
                >
                    Back
                </button>
                <button
                    onClick={onNext}
                    disabled={!canProceed}
                    className={`
                        w-2/3 py-2.5 rounded-lg font-medium text-[13px] transition-all shadow-sm
                        ${isDark
                            ? 'bg-white text-zinc-900 hover:bg-zinc-200 disabled:opacity-50 disabled:hover:bg-white cursor-not-allowed disabled:cursor-not-allowed'
                            : 'bg-zinc-900 text-white hover:bg-zinc-800 disabled:opacity-50 disabled:hover:bg-zinc-900 disabled:cursor-not-allowed'
                        }
                    `}
                >
                    Review Schema
                </button>
            </div>
        </div>
    );
}

function StepReview({ onBack, onSubmit, isSubmitting }) {
    const { isDark } = useTheme();
    const { name, database_type, connection_config, tables, getFormData } = usePluginForm();

    return (
        <div className="space-y-6">
            <div className={`
                p-6 rounded-2xl border space-y-6 relative overflow-hidden
                ${isDark ? 'bg-zinc-900/50 border-white/[0.08]' : 'bg-white border-zinc-200 shadow-sm'}
            `}>
                <div className="flex items-start justify-between">
                    <div>
                        <h2 className={`text-xl font-semibold tracking-tight ${isDark ? 'text-white' : 'text-zinc-900'}`}>{name}</h2>
                        <div className="flex items-center gap-4 mt-2">
                            <span className={`text-[12px] flex items-center gap-1.5 ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>
                                <Database className="w-3.5 h-3.5" /> {database_type}
                            </span>
                            <span className={`text-[12px] flex items-center gap-1.5 ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>
                                <Globe className="w-3.5 h-3.5" /> {connection_config.host}
                            </span>
                        </div>
                    </div>
                </div>

                <div className={`h-px w-full ${isDark ? 'bg-white/[0.06]' : 'bg-zinc-100'}`} />

                <div className="space-y-4">
                    <h3 className={`text-[13px] font-semibold uppercase tracking-wide ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>Schema Overview</h3>
                    <div className="grid gap-3">
                        {tables.map((table, idx) => (
                            <div key={idx} className={`p-4 rounded-xl border flex items-center justify-between ${isDark ? 'bg-white/[0.02] border-white/[0.04]' : 'bg-zinc-50 border-zinc-100'}`}>
                                <div className="flex items-center gap-3">
                                    <div className={`p-1.5 rounded-md ${isDark ? 'bg-emerald-500/10' : 'bg-emerald-50'}`}>
                                        <Table2 className={`w-4 h-4 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`} />
                                    </div>
                                    <span className={`text-sm font-semibold ${isDark ? 'text-zinc-300' : 'text-zinc-800'}`}>{table.table_name}</span>
                                </div>
                                <span className={`text-xs ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>{table.fields.length} attributes</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <div className="flex gap-3 pt-4 border-t border-zinc-200 dark:border-white/[0.05]">
                <button
                    type="button"
                    onClick={onBack}
                    disabled={isSubmitting}
                    className={`
                        w-1/3 py-2.5 rounded-lg font-medium text-[13px] transition-colors
                        ${isDark ? 'bg-white/5 text-zinc-300 hover:bg-white/10' : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'}
                    `}
                >
                    Back
                </button>
                <button
                    onClick={() => onSubmit(getFormData())}
                    disabled={isSubmitting}
                    className={`
                        w-2/3 py-2.5 rounded-lg font-medium text-[13px] transition-all shadow-sm flex items-center justify-center gap-2
                        ${isDark
                            ? 'bg-emerald-500 text-white hover:bg-emerald-400 disabled:opacity-50'
                            : 'bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50'
                        }
                    `}
                >
                    {isSubmitting ? (
                        <><Loader2 className="w-4 h-4 animate-spin" /> Deploying...</>
                    ) : (
                        'Deploy Plugin'
                    )}
                </button>
            </div>
        </div>
    );
}

// ============ Main Drawer ============

function CreatePluginModalContent({ onClose, onSuccess }) {
    const { isDark } = useTheme();
    const { step, nextStep, prevStep, reset } = usePluginForm();
    const createPlugin = useCreatePlugin();

    const handleSubmit = async (formData) => {
        try {
            await createPlugin.mutateAsync(formData);
            reset();
            onSuccess?.();
            onClose();
            toast.success('Plugin created successfully');
        } catch (error) {
            console.error('Submission Failed:', error);
            if (error.response?.data?.detail) {
                toast.error(error.response.data.detail[0]?.msg || 'Validation failed');
            } else {
                toast.error('Failed to create plugin');
            }
        }
    };

    const steps = [
        { title: 'Identity', component: StepBasicInfo },
        { title: 'Connection', component: StepConnection },
        { title: 'Schema', component: StepTables },
        { title: 'Deploy', component: StepReview },
    ];

    const CurrentStep = steps[step - 1].component;

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className={`p-6 border-b flex items-center justify-between ${isDark ? 'border-white/[0.06]' : 'border-zinc-200'}`}>
                <div>
                    <h2 className={`text-lg font-semibold tracking-tight ${isDark ? 'text-white' : 'text-zinc-900'}`}>
                        Create Plugin
                    </h2>
                    <p className={`text-xs mt-1 ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>
                        Configure a new ingestion pipeline
                    </p>
                </div>
                <button
                    onClick={onClose}
                    className={`p-2 rounded-md transition-colors ${isDark ? 'hover:bg-white/10 text-zinc-400' : 'hover:bg-zinc-100 text-zinc-500'}`}
                >
                    <X className="w-4 h-4" />
                </button>
            </div>

            {/* Stepper Progress */}
            <div className={`px-6 py-4 border-b flex items-center gap-2 ${isDark ? 'border-white/[0.06] bg-black/20' : 'border-zinc-100 bg-zinc-50/50'}`}>
                {steps.map((s, idx) => (
                    <div key={idx} className="flex flex-1 items-center gap-2">
                        <div className={`
                            w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold transition-colors
                            ${step > idx ? 'bg-emerald-500 text-white' : step === idx + 1 ? (isDark ? 'bg-white text-black' : 'bg-zinc-900 text-white') : (isDark ? 'bg-white/10 text-zinc-500' : 'bg-zinc-200 text-zinc-500')}
                        `}>
                            {step > idx + 1 ? <CheckCircle2 className="w-3 h-3" /> : idx + 1}
                        </div>
                        <span className={`text-[11px] font-medium hidden sm:block ${step === idx + 1 ? (isDark ? 'text-white' : 'text-zinc-900') : (isDark ? 'text-zinc-500' : 'text-zinc-400')}`}>
                            {s.title}
                        </span>
                        {idx < steps.length - 1 && (
                            <div className={`flex-1 h-px ml-2 ${isDark ? 'bg-white/10' : 'bg-zinc-200'}`} />
                        )}
                    </div>
                ))}
            </div>

            {/* Form Content */}
            <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={step}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
                    >
                        <CurrentStep
                            onNext={nextStep}
                            onBack={prevStep}
                            onSubmit={handleSubmit}
                            isSubmitting={createPlugin.isPending}
                        />
                    </motion.div>
                </AnimatePresence>
            </div>
        </div>
    );
}

import { createPortal } from 'react-dom';

export function CreatePluginModal({ isOpen, onClose, onSuccess }) {
    const { isDark } = useTheme();
    const modalRef = useRef(null);

    useEffect(() => {
        if (isOpen) modalRef.current?.focus();
    }, [isOpen]);

    const handleKeyDown = (e) => {
        if (e.key === 'Escape') onClose();
    };

    const modalContent = (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[500] flex justify-end overflow-hidden">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-zinc-950/60 backdrop-blur-sm"
                    />

                    <motion.div
                        ref={modalRef}
                        initial={{ x: '100%', filter: 'blur(10px)' }}
                        animate={{ x: 0, filter: 'blur(0px)' }}
                        exit={{ x: '100%', filter: 'blur(10px)' }}
                        transition={{ type: "spring", damping: 25, stiffness: 200 }}
                        onKeyDown={handleKeyDown}
                        tabIndex={-1}
                        role="dialog"
                        aria-modal="true"
                        className={`
                            relative z-10 w-full max-w-2xl h-full shadow-2xl border-l flex flex-col
                            ${isDark ? 'bg-[#0A0A0A] border-white/[0.08]' : 'bg-white border-zinc-200'}
                        `}
                    >
                        <PluginFormProvider>
                            <CreatePluginModalContent onClose={onClose} onSuccess={onSuccess} />
                        </PluginFormProvider>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );

    if (typeof document === 'undefined') return null;
    return createPortal(modalContent, document.body);
}

export default CreatePluginModal;
