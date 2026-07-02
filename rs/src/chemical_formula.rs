use regex::Regex;
use std::collections::VecDeque;

#[derive(Debug, Clone)]
pub enum ParsedElement {
    Element(String, i32),
}

#[derive(Debug, Clone)]
pub enum ParsedCount {
    Count(i32),
}

#[derive(Debug, Clone)]
pub enum ParsedGroup {
    Group(VecDeque<ParsedFormulaItem>),
}

#[derive(Debug, Clone)]
pub enum ParsedFormulaItem {
    Element(ParsedElement),
    Count(ParsedCount),
    Group(ParsedGroup),
}

pub type ParsedFormula = VecDeque<ParsedFormulaItem>;

pub fn parse_chemical_formula(formula: &str) -> ParsedFormula {
    let element_pattern = Regex::new(r"[A-Z][a-z]*").unwrap();

    fn digits(tokens: &mut Vec<&str>) -> i32 {
        if let Some(token) = tokens.pop() {
            if token.chars().all(|c| c.is_digit(10)) {
                return token.parse().unwrap();
            }
        }
        1
    }

    fn parse(tokens: &mut Vec<&str>, element_pattern: &Regex) -> ParsedFormula {
        let mut parsed: ParsedFormula = VecDeque::new();
        while let Some(token) = tokens.pop() {
            match token {
                "(" => {
                    let sub_parsed = parse(tokens, element_pattern);
                    let multiplier = digits(tokens);
                    parsed.push_back(ParsedFormulaItem::Group(ParsedGroup::Group(
                        sub_parsed.into_iter().collect(),
                    )));
                    parsed.push_back(ParsedFormulaItem::Count(ParsedCount::Count(multiplier)));
                }
                ")" => break,
                _ if element_pattern.is_match(token) => {
                    let element = token.to_string();
                    let count = digits(tokens);
                    parsed.push_back(ParsedFormulaItem::Element(ParsedElement::Element(
                        element, count,
                    )));
                }
                _ => (),
            }
        }
        parsed
    }

    let tokens: Vec<&str> = formula.split("").collect::<Vec<&str>>();
    let parsed = parse(
        &mut tokens[1..].iter().rev().cloned().collect::<Vec<&str>>(),
        &element_pattern,
    );
    _unparse_check(formula, &parsed);
    parsed
}

fn _unparse_check(formula: &str, parsed: &ParsedFormula) {
    fn _remove_digit_check(formula: &str, cell: &str) -> bool {
        if formula.len() > cell.len() {
            formula.chars().nth(cell.len()).unwrap().is_digit(10)
        } else {
            false
        }
    }

    fn unparse(parse: &ParsedFormula, formula: &str) -> String {
        let mut result = formula.to_string();
        for p in parse.into_iter() {
            match p {
                ParsedFormulaItem::Element(ParsedElement::Element(element, count)) => {
                    if _remove_digit_check(&result, element) {
                        result = result.replace(&count.to_string(), "");
                    }
                    result = result.replace(element, "");
                }
                ParsedFormulaItem::Group(ParsedGroup::Group(group)) => {
                    result = result.replace("(", "");
                    result = unparse(group, &result);
                }
                ParsedFormulaItem::Count(ParsedCount::Count(count)) => {
                    if _remove_digit_check(&result, ")") {
                        result = result.replace(&count.to_string(), "");
                    }
                    result = result.replace(")", "");
                }
            }
        }
        result
    }

    let formula = formula.replace(" ", "");
    if !unparse(parsed, &formula).is_empty() {
        panic!(
            "Unparsed chemical equation symbols '{}'",
            unparse(parsed, &formula)
        );
    }
}
