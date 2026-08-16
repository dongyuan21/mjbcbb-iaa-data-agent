#!/usr/bin/env ruby
# encoding: UTF-8
# frozen_string_literal: true

require "find"
require "pathname"

root = Pathname.new(__dir__).parent
local_private_dirs = %w[skill-ignore 术语解释].freeze
forbidden_parts = %w[raw raw_exports audit_archive private staging cache snapshots metadata tables table_cards skill-ignore 术语解释].freeze
forbidden_extensions = %w[.sql .csv .tsv .xlsx .xls .docx .pdf .yaml .yml .jsonl].freeze
patterns = {
  "凭证赋值" => /(?i)(access[_ -]?key|secret[_ -]?key|password|passwd|token|cookie|authorization)\s*[:=]\s*(?!<已脱敏>)[^\s]+/,
  "邮箱" => /\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b/,
  "本地绝对路径" => %r{(?:/Users/|/home/)[^\s"'<>]+},
  "IP 地址" => /(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])/,
  "私有域名" => /(?i)youxi123\.com/
}.freeze

violations = []
root.find do |path|
  relative = path.relative_path_from(root).to_s.force_encoding(Encoding::UTF_8).scrub
  next if relative.start_with?(".git/") || relative == "scripts/校验公开快照.rb"
  if path.directory?
    if local_private_dirs.include?(relative)
      Find.prune
      next
    end
    if relative.split(File::SEPARATOR).any? { |part| forbidden_parts.include?(part.downcase) }
      violations << "禁止目录：#{relative}"
      Find.prune
    else
      next
    end
  end
  if forbidden_extensions.include?(path.extname.downcase)
    violations << "禁止文件类型：#{relative}"
    next
  end
  next unless path.file? && path.size <= 3 * 1024 * 1024
  content = path.binread
  next if content.include?("\x00")
  text = content.force_encoding(Encoding::UTF_8).scrub.encode(Encoding::UTF_8)
  patterns.each { |name, pattern| violations << "#{name}：#{relative}" if text.match?(pattern) }
end

abort("公开快照校验失败：\n- #{violations.join("\n- ")}") unless violations.empty?
puts "公开快照校验通过"
