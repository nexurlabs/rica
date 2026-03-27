import React, { useState, useRef, useEffect } from 'react';

interface Option {
    label: string;
    value: string;
}

interface DropdownProps {
    value: string;
    onChange: (value: string) => void;
    options: Option[];
    className?: string;
}

export function Dropdown({ value, onChange, options, className = "" }: DropdownProps) {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const selectedOption = options.find((opt) => opt.value === value) || options[0];

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
        <div ref={dropdownRef} className={`relative inline-block text-sm ${className}`}>
            <button
                type="button"
                className="flex items-center justify-between gap-2 px-3 py-1.5 rounded-lg transition-all duration-200"
                style={{
                    background: "var(--bg-primary)",
                    color: "var(--text-primary)",
                    border: `1px solid ${isOpen ? "var(--accent)" : "var(--border)"}`,
                    minWidth: "110px"
                }}
                onClick={() => setIsOpen(!isOpen)}
            >
                <span>{selectedOption?.label}</span>
                <span style={{ fontSize: "10px", color: "var(--text-secondary)", transition: "transform 0.2s", transform: isOpen ? "rotate(180deg)" : "rotate(0deg)" }}>
                    ▼
                </span>
            </button>

            {isOpen && (
                <div
                    className="absolute right-0 mt-2 py-1 rounded-lg z-50 shadow-xl fade-in"
                    style={{
                        background: "var(--bg-card)",
                        border: "1px solid var(--border)",
                        minWidth: "100%",
                        maxHeight: "300px",
                        overflowY: "auto",
                        animationDuration: "0.15s"
                    }}
                >
                    {options.map((option) => (
                        <button
                            key={option.value}
                            type="button"
                            className="block w-full text-left px-4 py-2 hover:bg-[rgba(108,92,231,0.15)] transition-colors"
                            style={{
                                color: option.value === value ? "var(--accent-light)" : "var(--text-primary)",
                                fontWeight: option.value === value ? 600 : 400
                            }}
                            onClick={() => {
                                onChange(option.value);
                                setIsOpen(false);
                            }}
                        >
                            {option.label}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
