// src/components/ui/Input.jsx
const Input = ({ value, onChange, placeholder, readOnly, className }) => {
    return (
      <input
        type="text"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        readOnly={readOnly}
        className={className}
      />
    );
  };
  
  export default Input;
  