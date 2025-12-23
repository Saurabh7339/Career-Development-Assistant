import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism';

const MarkdownRenderer = ({ content }) => {
  return (
    <div className="prose prose-lg max-w-none">
      <ReactMarkdown
        components={{
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            return !inline && match ? (
              <SyntaxHighlighter
                style={vscDarkPlus}
                language={match[1]}
                PreTag="div"
                {...props}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
          table({ children }) {
            return (
              <div className="overflow-x-auto my-4">
                <table className="min-w-full divide-y divide-gray-200 border border-gray-300">
                  {children}
                </table>
              </div>
            );
          },
          thead({ children }) {
            return <thead className="bg-gray-50">{children}</thead>;
          },
          th({ children }) {
            return (
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider border border-gray-300">
                {children}
              </th>
            );
          },
          td({ children }) {
            return (
              <td className="px-4 py-3 text-sm text-gray-700 border border-gray-300">
                {children}
              </td>
            );
          },
          h1({ children }) {
            return <h1 className="text-3xl font-bold text-gray-800 mt-6 mb-4">{children}</h1>;
          },
          h2({ children }) {
            return <h2 className="text-2xl font-semibold text-gray-800 mt-5 mb-3">{children}</h2>;
          },
          h3({ children }) {
            return <h3 className="text-xl font-semibold text-gray-800 mt-4 mb-2">{children}</h3>;
          },
          p({ children }) {
            return <p className="text-gray-700 mb-3 leading-relaxed">{children}</p>;
          },
          ul({ children }) {
            return <ul className="list-disc list-inside mb-3 space-y-1 text-gray-700">{children}</ul>;
          },
          ol({ children }) {
            return <ol className="list-decimal list-inside mb-3 space-y-1 text-gray-700">{children}</ol>;
          },
          li({ children }) {
            return <li className="ml-4">{children}</li>;
          },
          strong({ children }) {
            return <strong className="font-semibold text-gray-800">{children}</strong>;
          },
          em({ children }) {
            return <em className="italic text-gray-700">{children}</em>;
          },
          blockquote({ children }) {
            return (
              <blockquote className="border-l-4 border-primary-500 pl-4 italic text-gray-600 my-4">
                {children}
              </blockquote>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;

