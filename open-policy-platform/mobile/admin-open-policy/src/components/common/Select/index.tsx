import { useState, useRef, useEffect } from "react";
import { IoChevronDownOutline } from "react-icons/io5";

interface Option {
  value: string;
  label: string;
}

interface SelectProps {
  options: Option[];
  placeholder: string;
  value?: string;
  onChange?: (value: string) => void;
  className?: string;
  width?: string;
}

const Select = ({
  options,
  placeholder,
  // value,
  onChange,
  className = "",
  width = "w-[200px]",
}: SelectProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedOption, setSelectedOption] = useState<Option | null>(null);
  const selectRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        selectRef.current &&
        !selectRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (option: Option) => {
    setSelectedOption(option);
    setIsOpen(false);
    onChange?.(option.value);
  };

  return (
    <div ref={selectRef} className={`relative ${width} ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center justify-between w-full h-[40px] px-3 bg-white border border-[#EDEDED] rounded-[8px] text-[#515151] text-sm ${
          isOpen ? "border-[#628ECB]" : ""
        }`}
      >
        <span className="truncate">
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <IoChevronDownOutline
          className={`transition-transform ${isOpen ? "rotate-180" : ""}`}
        />
      </button>

      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-[#EDEDED] rounded-[8px] shadow-lg max-h-[200px] overflow-y-auto">
          {options.map((option) => (
            <button
              key={option.value}
              onClick={() => handleSelect(option)}
              className={`w-full px-3 py-2 text-left text-sm hover:bg-[#F5F5F5] ${
                selectedOption?.value === option.value
                  ? "bg-[#F5F5F5] text-[#628ECB]"
                  : "text-[#515151]"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default Select;
